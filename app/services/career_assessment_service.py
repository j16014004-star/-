"""Stage assessment lifecycle for accepted career plans."""
from __future__ import annotations

import hashlib
import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.career_assessment_agent import CareerAssessmentAgent
from app.core.config import settings
from app.crud.ai_task import claim_provider_call, create_ai_task, get_ai_task
from app.crud.career_assessment import (
    get_assessment, get_assessment_answers, get_assessment_questions,
    get_owned_assessment, get_reusable_assessment, get_stage_progresses,
)
from app.crud.career_plan import get_execution_by_id, get_execution_tasks, get_plan
from app.models.ai import AITask
from app.models.user import User
from app.models.career_plan import (
    CareerPlanExecutionTask, CareerStageAssessment, CareerStageAssessmentAnswer,
    CareerStageAssessmentQuestion, CareerPlanQuestion,
)
from app.schemas.career_plan import CareerAssessmentSubmitRequest
from app.services.career_execution_service import (
    build_execution_overview, ensure_stage_progress, serialize_execution_task,
    today_in_china, utc_now_naive,
)
from app.services.career_plan_service import CareerPlanError, serialize_plan
from app.workers.process_launcher import WorkerLaunchError, launch_ai_task_worker

PROMPT_VERSION = "career-stage-assessment-v1"


def serialize_question(item: CareerStageAssessmentQuestion, *, include_answer=False) -> dict:
    data = {"id": item.id, "question_order": item.question_order, "type": item.question_type,
            "title": item.title, "options": item.options or [], "points": item.points,
            "code_language": item.code_language}
    if include_answer:
        data.update({"correct_answer": item.correct_answer, "reference_answer": item.reference_answer, "rubric": item.rubric})
    return data


async def create_stage_assessment(db: AsyncSession, *, user_id: int, execution_plan_id: int) -> dict:
    await db.execute(select(User.id).where(User.id == user_id).with_for_update())
    execution = await get_execution_by_id(db, execution_plan_id, user_id)
    if execution is None:
        raise CareerPlanError("执行计划不存在", 404)
    overview = await build_execution_overview(db, execution=execution, user_id=user_id)
    if not overview["assessment_ready"]:
        raise CareerPlanError("当前阶段尚未达到考核条件", 409)
    stages = await ensure_stage_progress(db, execution=execution, user_id=user_id)
    stage = next((item for item in stages if item.status not in ("locked", "passed")), None)
    if stage is None:
        raise CareerPlanError("没有可考核的阶段", 409)
    reusable = await get_reusable_assessment(db, execution.id, stage.stage_order, user_id)
    if reusable:
        task_id = reusable.generation_task_id if reusable.status in ("generating", "ready") else reusable.evaluation_task_id
        task = await get_ai_task(db, task_id) if task_id else None
        return _start_response(reusable, task)
    assessment = CareerStageAssessment(user_id=user_id, execution_plan_id=execution.id,
        stage_progress_id=stage.id, stage=stage.stage, stage_order=stage.stage_order,
        status="generating", passing_score=70)
    db.add(assessment)
    await db.flush()
    task = _new_task(user_id, "career_stage_assessment", assessment.id)
    await create_ai_task(db, task)
    assessment.generation_task_id = task.id
    stage.status = "assessing"
    await db.commit()
    try:
        launch_ai_task_worker(task.id)
    except WorkerLaunchError as exc:
        task.status, task.error_message = "failed", "无法启动阶段考核 AI worker"
        assessment.status, assessment.error_message = "failed", task.error_message
        await db.commit()
        raise CareerPlanError(task.error_message, 503) from exc
    return _start_response(assessment, task)


def _new_task(user_id: int, task_type: str, assessment_id: int) -> AITask:
    digest = hashlib.sha256(f"{task_type}:{assessment_id}".encode()).hexdigest()
    return AITask(id=str(uuid.uuid4()), user_id=user_id, task_type=task_type,
        resource_type="career_stage_assessment", resource_id=assessment_id,
        status="pending", progress=0, model_name=settings.CAREER_PLANNING_MODEL,
        prompt_version=PROMPT_VERSION, input_hash=digest,
        request_payload={"assessment_id": assessment_id})


def _start_response(assessment, task):
    return {"assessment_id": assessment.id, "task_id": task.id if task else None,
            "status": assessment.status, "result_id": task.result_id if task else None,
            "poll_after_seconds": 1}


async def get_stage_assessment_detail(db: AsyncSession, *, user_id: int, assessment_id: int) -> dict:
    assessment = await get_owned_assessment(db, assessment_id, user_id)
    if assessment is None:
        raise CareerPlanError("阶段考核不存在", 404)
    questions = await get_assessment_questions(db, assessment.id)
    return {"id": assessment.id, "execution_plan_id": assessment.execution_plan_id,
            "stage": assessment.stage, "stage_order": assessment.stage_order,
            "status": assessment.status, "passing_score": assessment.passing_score,
            "time_limit_minutes": assessment.time_limit_minutes,
            "questions": [serialize_question(item) for item in questions],
            "created_at": assessment.created_at}


async def submit_stage_assessment(db: AsyncSession, *, user_id: int, assessment_id: int, request: CareerAssessmentSubmitRequest) -> dict:
    await db.execute(select(User.id).where(User.id == user_id).with_for_update())
    assessment = await get_owned_assessment(db, assessment_id, user_id)
    if assessment is None:
        raise CareerPlanError("阶段考核不存在", 404)
    if assessment.status != "ready":
        raise CareerPlanError("该考核不可重复提交或尚未生成完成", 409)
    questions = await get_assessment_questions(db, assessment.id)
    supplied = {item.question_id: item.answer for item in request.answers}
    if set(supplied) != {item.id for item in questions}:
        raise CareerPlanError("必须一次提交全部考核题答案", 422)
    for question in questions:
        answer = supplied[question.id]
        rule_score = _objective_score(question, answer)
        db.add(CareerStageAssessmentAnswer(assessment_id=assessment.id, question_id=question.id,
            user_id=user_id, answer=answer, rule_score=rule_score,
            final_score=rule_score, scoring_rationale="按标准答案精确匹配" if rule_score is not None else None))
    task = _new_task(user_id, "career_stage_assessment_evaluation", assessment.id)
    await create_ai_task(db, task)
    assessment.evaluation_task_id = task.id
    assessment.status = "evaluating"
    assessment.submitted_at = utc_now_naive()
    await db.commit()
    try:
        launch_ai_task_worker(task.id)
    except WorkerLaunchError as exc:
        task.status, task.error_message = "failed", "无法启动阶段考核评阅 AI worker"
        assessment.status, assessment.error_message = "failed", task.error_message
        await db.commit()
        raise CareerPlanError(task.error_message, 503) from exc
    return _start_response(assessment, task)


def _objective_score(question, answer):
    if question.question_type not in ("choice", "multiple"):
        return None
    expected = question.correct_answer
    if question.question_type == "multiple":
        actual_set = {str(item) for item in answer} if isinstance(answer, list) else {str(answer)}
        expected_set = {str(item) for item in expected} if isinstance(expected, list) else {str(expected)}
        return question.points if actual_set == expected_set else 0
    return question.points if str(answer) == str(expected) else 0


async def get_stage_assessment_result(db: AsyncSession, *, user_id: int, assessment_id: int) -> dict:
    assessment = await get_owned_assessment(db, assessment_id, user_id)
    if assessment is None:
        raise CareerPlanError("阶段考核不存在", 404)
    if assessment.status not in ("passed", "needs_improvement"):
        raise CareerPlanError("考核结果尚未生成", 409)
    return {"assessment_id": assessment.id, "status": assessment.status, "score": assessment.score,
            "passing_score": assessment.passing_score, "passed": assessment.status == "passed",
            "summary": assessment.summary, "strengths": assessment.strengths or [],
            "weaknesses": assessment.weaknesses or [], "improvement_advice": assessment.improvement_advice or [],
            "question_results": assessment.question_results or [],
            "remediation_available": assessment.status == "needs_improvement"}


async def activate_next_stage(db: AsyncSession, *, user_id: int, assessment_id: int) -> dict:
    await db.execute(select(User.id).where(User.id == user_id).with_for_update())
    assessment = await get_owned_assessment(db, assessment_id, user_id)
    if assessment is None:
        raise CareerPlanError("阶段考核不存在", 404)
    if assessment.status != "passed":
        raise CareerPlanError("通过阶段考核后才能进入下一阶段", 409)
    execution = await get_execution_by_id(db, assessment.execution_plan_id, user_id)
    stages = await get_stage_progresses(db, execution.id, user_id)
    current = next(item for item in stages if item.id == assessment.stage_progress_id)
    current.status = "passed"
    current.passed_at = current.passed_at or utc_now_naive()
    next_stage = next((item for item in stages if item.stage_order > current.stage_order), None)
    tasks = await get_execution_tasks(db, execution.id, user_id)
    if next_stage:
        if next_stage.status == "locked":
            next_stage.status = "in_progress"
            for task in tasks:
                if task.stage_order == next_stage.stage_order:
                    task.is_active = True
    else:
        execution.status = "completed"
        execution.end_date = today_in_china()
    await db.flush()
    return await build_execution_overview(db, execution=execution, user_id=user_id)


async def create_remediation(db: AsyncSession, *, user_id: int, assessment_id: int) -> dict:
    await db.execute(select(User.id).where(User.id == user_id).with_for_update())
    assessment = await get_owned_assessment(db, assessment_id, user_id)
    if assessment is None:
        raise CareerPlanError("阶段考核不存在", 404)
    if assessment.status != "needs_improvement":
        raise CareerPlanError("仅未通过的考核可生成补强任务", 409)
    execution = await get_execution_by_id(db, assessment.execution_plan_id, user_id)
    tasks = await get_execution_tasks(db, execution.id, user_id)
    existing = [item for item in tasks if item.remediation_assessment_id == assessment.id]
    if not existing:
        advice = (assessment.improvement_advice or assessment.weaknesses or ["复盘本阶段错题并重新完成阶段实践"] )[:5]
        for index, text in enumerate(advice):
            db.add(CareerPlanExecutionTask(user_id=user_id, execution_plan_id=execution.id,
                task_key=hashlib.sha256(f"remediation:{assessment.id}:{index}".encode()).hexdigest(),
                title=f"补强任务：{str(text)[:220]}", description="根据阶段考核结果完成补强并记录实践证据",
                task_type="practice", stage=assessment.stage, stage_order=assessment.stage_order,
                task_order=10000 + index, week_no=max((item.week_no for item in tasks), default=1),
                planned_date=today_in_china() + timedelta(days=index), is_required=True,
                is_active=True, is_remediation=True, remediation_assessment_id=assessment.id, status="pending"))
    await db.flush()
    return await build_execution_overview(db, execution=execution, user_id=user_id)


async def execute_stage_assessment_task(task_id: str) -> None:
    from app.core.database import async_session
    async with async_session() as db:
        task = await get_ai_task(db, task_id)
        if task is None or task.status != "pending": return
        assessment = await get_assessment(db, task.resource_id)
        if assessment is None: return
        task.status, task.progress, task.started_at = "generating", 20, utc_now_naive()
        await claim_provider_call(db, task, utc_now_naive())
        context = await _assessment_context(db, assessment)
        await db.commit()
    try:
        state = await CareerAssessmentAgent().run(mode="generate", context=context)
        generated = state["result"]
        async with async_session() as db:
            task = await get_ai_task(db, task_id); assessment = await get_assessment(db, task.resource_id)
            points = _normalize_points([item.points for item in generated.questions])
            for index, (item, point) in enumerate(zip(generated.questions, points), 1):
                db.add(CareerStageAssessmentQuestion(assessment_id=assessment.id, question_order=index,
                    question_type=item.question_type, title=item.title, options=item.options,
                    correct_answer=item.correct_answer, reference_answer=item.reference_answer,
                    rubric=item.rubric, points=point, code_language=item.code_language))
            assessment.status, assessment.time_limit_minutes = "ready", generated.time_limit_minutes
            assessment.retrieval_audit = {
                **(assessment.retrieval_audit or {}),
                "generation": {
                    "source": state.get("retrieval_source") or "unknown",
                    "error": state.get("retrieval_error"),
                    "results": state.get("retrieval_audit") or [],
                },
            }
            task.status, task.progress, task.result_id, task.token_usage = "success", 100, assessment.id, state.get("token_usage")
            task.model_name = (
                state.get("used_model_name")
                or getattr(task, "model_name", None)
                or settings.CAREER_PLANNING_MODEL
            )
            task.finished_at = utc_now_naive()
            await db.commit()
    except Exception as exc:
        await _mark_failed(task_id, str(exc)); raise


async def execute_stage_assessment_evaluation_task(task_id: str) -> None:
    from app.core.database import async_session
    async with async_session() as db:
        task = await get_ai_task(db, task_id)
        if task is None or task.status != "pending": return
        assessment = await get_assessment(db, task.resource_id)
        questions = await get_assessment_questions(db, assessment.id)
        answers = await get_assessment_answers(db, assessment.id)
        answer_map = {item.question_id: item for item in answers}
        context = {"questions": [{**serialize_question(q, include_answer=True), "user_answer": answer_map[q.id].answer} for q in questions if q.question_type in ("short", "code")]}
        task.status, task.progress, task.started_at = "generating", 20, utc_now_naive()
        await claim_provider_call(db, task, utc_now_naive()); await db.commit()
    try:
        state = await CareerAssessmentAgent().run(mode="evaluate", context=context)
        result = state["result"]
        async with async_session() as db:
            task = await get_ai_task(db, task_id); assessment = await get_assessment(db, task.resource_id)
            questions = await get_assessment_questions(db, assessment.id); answers = await get_assessment_answers(db, assessment.id)
            qmap, amap = {q.id: q for q in questions}, {a.question_id: a for a in answers}
            subjective = {item.question_id: item for item in result.subjective_results}
            details, total = [], 0
            for qid, answer in amap.items():
                if answer.rule_score is None:
                    judged = subjective.get(qid)
                    answer.ai_score = min(qmap[qid].points, judged.score if judged else 0)
                    answer.final_score = answer.ai_score
                    answer.scoring_rationale = judged.rationale if judged else "AI 未返回该题评分，按 0 分处理"
                total += answer.final_score or 0
                details.append({"question_id": qid, "score": answer.final_score or 0, "max_score": qmap[qid].points, "rationale": answer.scoring_rationale})
            assessment.score = max(0, min(100, total)); assessment.summary = result.summary
            assessment.strengths, assessment.weaknesses = result.strengths, result.weaknesses
            assessment.improvement_advice, assessment.question_results = result.improvement_advice, details
            assessment.retrieval_audit = {
                **(assessment.retrieval_audit or {}),
                "evaluation": {
                    "source": state.get("retrieval_source") or "unknown",
                    "error": state.get("retrieval_error"),
                    "results": state.get("retrieval_audit") or [],
                },
            }
            assessment.status = "passed" if assessment.score >= assessment.passing_score else "needs_improvement"
            assessment.evaluated_at = utc_now_naive()
            stages = await get_stage_progresses(db, assessment.execution_plan_id, assessment.user_id)
            stage = next(item for item in stages if item.id == assessment.stage_progress_id)
            stage.status = assessment.status
            task.status, task.progress, task.result_id, task.token_usage = "success", 100, assessment.id, state.get("token_usage")
            task.model_name = (
                state.get("used_model_name")
                or getattr(task, "model_name", None)
                or settings.CAREER_PLANNING_MODEL
            )
            task.finished_at = utc_now_naive(); await db.commit()
    except Exception as exc:
        await _mark_failed(task_id, str(exc)); raise


async def _assessment_context(db, assessment):
    execution = await get_execution_by_id(db, assessment.execution_plan_id, assessment.user_id)
    plan = await get_plan(db, execution.career_plan_id, assessment.user_id)
    tasks = await get_execution_tasks(db, execution.id, assessment.user_id)
    stage_tasks = [item for item in tasks if item.stage_order == assessment.stage_order]
    task_ids = [item.id for item in stage_tasks]
    questions = []
    if task_ids:
        result = await db.execute(select(CareerPlanQuestion).where(
            CareerPlanQuestion.user_id == assessment.user_id,
            CareerPlanQuestion.execution_task_id.in_(task_ids),
            CareerPlanQuestion.status == "answered",
        ))
        questions = [{"question": item.question, "answer": item.answer} for item in result.scalars().all()]
    return {"stage": assessment.stage, "plan": serialize_plan(plan),
            "stage_tasks": [serialize_execution_task(item) for item in stage_tasks],
            "stage_questions_and_answers": questions}


def _normalize_points(points):
    if not points:
        return []
    total = sum(points) or len(points)
    normalized = [max(1, int(item * 100 / total)) for item in points]
    while sum(normalized) < 100:
        index = max(range(len(points)), key=lambda i: points[i] * 100 / total - normalized[i])
        normalized[index] += 1
    while sum(normalized) > 100:
        index = max((i for i in range(len(points)) if normalized[i] > 1), key=lambda i: normalized[i])
        normalized[index] -= 1
    return normalized


async def _mark_failed(task_id, message):
    from app.core.database import async_session
    async with async_session() as db:
        task = await get_ai_task(db, task_id)
        if not task: return
        assessment = await get_assessment(db, task.resource_id)
        task.status, task.progress, task.error_message, task.finished_at = "failed", 100, message[:500], utc_now_naive()
        if assessment: assessment.status, assessment.error_message = "failed", message[:500]
        await db.commit()
