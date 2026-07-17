"""Application service for AI mock interviews."""
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.knowledge import infer_knowledge_role
from app.ai.mock_interview_agent import MockInterviewAgent
from app.core.config import settings
from app.models.ai import ResumeOptimizationVersion
from app.models.job import Job, JobApplication
from app.models.mock_interview import (
    MockInterview,
    MockInterviewAnswer,
    MockInterviewQuestion,
    MockInterviewQuestionRecommendation,
    MockInterviewReport,
)
from app.models.resume import Resume
from app.schemas.mock_interview import MockInterviewAnswerRequest, MockInterviewCreateRequest


class MockInterviewError(ValueError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def get_interview_options(db: AsyncSession, *, user_id: int) -> dict:
    applications = (
        await db.execute(
            select(JobApplication, Job)
            .join(Job, Job.id == JobApplication.job_id)
            .where(JobApplication.user_id == user_id)
            .order_by(JobApplication.applied_at.desc())
        )
    ).all()
    resumes = (
        await db.execute(
            select(Resume)
            .where(Resume.user_id == user_id, Resume.status == "completed")
            .order_by(Resume.updated_at.desc())
        )
    ).scalars().all()
    optimized = (
        await db.execute(
            select(ResumeOptimizationVersion)
            .where(
                ResumeOptimizationVersion.user_id == user_id,
                ResumeOptimizationVersion.is_saved.is_(True),
            )
            .order_by(ResumeOptimizationVersion.saved_at.desc())
        )
    ).scalars().all()
    return {
        "applied_jobs": [
            {
                "application_id": app.id,
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "description": job.description,
                "resume_id": app.resume_id,
                "resume_source": app.resume_source,
                "resume_optimization_id": app.resume_optimization_id,
            }
            for app, job in applications
        ],
        "resumes": [
            {"id": item.id, "title": item.title or f"简历 {item.id}", "updated_at": item.updated_at}
            for item in resumes
        ],
        "optimized_resumes": [
            {
                "id": item.id,
                "resume_id": item.resume_id,
                "title": item.title or f"优化简历 {item.id}",
                "target_role": item.target_role,
                "saved_at": item.saved_at,
            }
            for item in optimized
        ],
        "supported_domains": [
            {"value": "python_backend", "label": "Python 后端开发"},
            {"value": "secretary_studies", "label": "秘书学 / 行政文秘"},
        ],
    }


async def create_mock_interview(
    db: AsyncSession, *, user_id: int, request: MockInterviewCreateRequest,
    agent_factory=MockInterviewAgent,
) -> MockInterview:
    role = request.target_role
    company = request.company
    job_description = request.job_description
    resume_id = request.resume_id
    resume_source = request.resume_source
    optimization_id = request.resume_optimization_id

    if request.source_type == "applied":
        row = (
            await db.execute(
                select(JobApplication, Job)
                .join(Job, Job.id == JobApplication.job_id)
                .where(
                    JobApplication.user_id == user_id,
                    JobApplication.job_id == request.job_id,
                )
            )
        ).first()
        if not row:
            raise MockInterviewError("未找到该用户的岗位投递记录", 404)
        application, job = row
        role = job.title
        company = job.company
        job_description = job.description
        resume_id = application.resume_id
        resume_source = application.resume_source
        optimization_id = application.resume_optimization_id

    resume_text = await _load_resume_text(
        db, user_id=user_id, resume_id=resume_id, resume_source=resume_source,
        optimization_id=optimization_id,
    )
    domain = infer_knowledge_role(role, job_description, resume_text)
    if domain not in {"python_backend", "secretary_studies"}:
        raise MockInterviewError("当前模拟面试仅支持 Python 后端开发和秘书学方向", 422)
    title = request.title or f"{role}模拟面试"
    context = {
        "domain": domain,
        "target_role": role,
        "company": company,
        "job_description": (job_description or "")[:10000],
        "resume_text": resume_text[:12000],
        "difficulty": request.difficulty,
        "question_types": request.question_types,
        "question_count": request.question_count,
        "focus_weaknesses": request.focus_weaknesses,
    }
    state = await agent_factory(domain=domain).run(mode="questions", context=context)
    generated = state["result"]
    interview = MockInterview(
        user_id=user_id,
        source_type=request.source_type,
        job_id=request.job_id,
        resume_id=resume_id,
        resume_source=resume_source,
        resume_optimization_id=optimization_id,
        title=title,
        target_role=role or "",
        company=company,
        job_description=job_description,
        domain=domain,
        difficulty=request.difficulty,
        question_types=request.question_types,
        question_count=len(generated.questions),
        status="pending",
        current_question_order=1,
        retrieval_source=state.get("retrieval_source"),
        retrieval_error=state.get("retrieval_error"),
        retrieval_audit=state.get("retrieval_audit"),
        model_name=state.get("used_model_name"),
        token_usage=state.get("token_usage"),
        prompt_version=settings.MOCK_INTERVIEW_PROMPT_VERSION,
    )
    db.add(interview)
    await db.flush()
    chunk_ids = [item.get("chunk_id", "") for item in state.get("retrieval_audit") or []]
    for index, item in enumerate(generated.questions, start=1):
        db.add(MockInterviewQuestion(
            interview_id=interview.id,
            order_no=index,
            question_type=item.question_type,
            question=item.question.strip(),
            intent=item.intent.strip(),
            difficulty=item.difficulty,
            reference_points=item.reference_points,
            rubric=item.rubric,
            knowledge_chunk_ids=chunk_ids,
            status="pending",
        ))
    await db.flush()
    return interview


async def list_mock_interviews(db: AsyncSession, *, user_id: int) -> list[dict]:
    items = (
        await db.execute(
            select(MockInterview)
            .where(MockInterview.user_id == user_id)
            .order_by(MockInterview.created_at.desc())
        )
    ).scalars().all()
    return [serialize_interview(item) for item in items]


async def get_mock_interview(
    db: AsyncSession, *, user_id: int, interview_id: int, include_answers: bool = True,
) -> dict:
    interview = await _get_owned_interview(db, user_id, interview_id)
    questions = (
        await db.execute(
            select(MockInterviewQuestion)
            .where(MockInterviewQuestion.interview_id == interview.id)
            .order_by(MockInterviewQuestion.order_no)
        )
    ).scalars().all()
    answers_by_question: dict[int, MockInterviewAnswer] = {}
    if include_answers:
        answers = (
            await db.execute(
                select(MockInterviewAnswer)
                .join(MockInterviewQuestion, MockInterviewQuestion.id == MockInterviewAnswer.question_id)
                .where(MockInterviewQuestion.interview_id == interview.id)
            )
        ).scalars().all()
        answers_by_question = {item.question_id: item for item in answers}
    result = serialize_interview(interview)
    result["questions"] = [
        serialize_question(item, answers_by_question.get(item.id)) for item in questions
    ]
    return result


async def start_mock_interview(db: AsyncSession, *, user_id: int, interview_id: int) -> dict:
    interview = await _get_owned_interview(db, user_id, interview_id)
    if interview.status == "completed":
        raise MockInterviewError("该面试已经完成", 409)
    if interview.status == "pending":
        interview.status = "in_progress"
        interview.started_at = utc_now()
    await db.flush()
    return await get_mock_interview(db, user_id=user_id, interview_id=interview_id)


async def get_next_question(db: AsyncSession, *, user_id: int, interview_id: int) -> dict | None:
    interview = await _get_owned_interview(db, user_id, interview_id)
    question = (
        await db.execute(
            select(MockInterviewQuestion)
            .where(
                MockInterviewQuestion.interview_id == interview.id,
                MockInterviewQuestion.status == "pending",
            )
            .order_by(MockInterviewQuestion.order_no)
            .limit(1)
        )
    ).scalar_one_or_none()
    return serialize_question(question) if question else None


async def submit_mock_interview_answer(
    db: AsyncSession, *, user_id: int, interview_id: int,
    request: MockInterviewAnswerRequest, agent_factory=MockInterviewAgent,
) -> dict:
    interview = await _get_owned_interview(db, user_id, interview_id)
    if interview.status == "completed":
        raise MockInterviewError("该面试已经结束", 409)
    question = (
        await db.execute(
            select(MockInterviewQuestion).where(
                MockInterviewQuestion.id == request.question_id,
                MockInterviewQuestion.interview_id == interview.id,
            )
        )
    ).scalar_one_or_none()
    if not question:
        raise MockInterviewError("面试题不存在", 404)
    existing = (
        await db.execute(
            select(MockInterviewAnswer).where(MockInterviewAnswer.question_id == question.id)
        )
    ).scalar_one_or_none()
    if existing:
        raise MockInterviewError("该题已经提交，不能重复评分", 409)
    if interview.status == "pending":
        interview.status = "in_progress"
        interview.started_at = utc_now()
    context = {
        "domain": interview.domain,
        "target_role": interview.target_role,
        "job_description": interview.job_description or "",
        "question": question.question,
        "intent": question.intent,
        "reference_points": question.reference_points,
        "rubric": question.rubric,
        "answer": request.answer,
    }
    state = await agent_factory(domain=interview.domain).run(mode="evaluate", context=context)
    evaluation = state["result"]
    answer = MockInterviewAnswer(
        question_id=question.id,
        user_id=user_id,
        answer_text=request.answer,
        duration_seconds=request.duration_seconds,
        score=evaluation.score,
        dimension_scores=evaluation.dimension_scores,
        matched_points=evaluation.matched_points,
        missing_points=evaluation.missing_points,
        feedback=evaluation.feedback,
        follow_up_question=evaluation.follow_up_question,
        model_name=state.get("used_model_name"),
        token_usage=state.get("token_usage"),
    )
    db.add(answer)
    question.status = "answered"
    if evaluation.follow_up_question and evaluation.score < 70:
        follow_up_count = int((
            await db.execute(
                select(func.count(MockInterviewQuestion.id)).where(
                    MockInterviewQuestion.interview_id == interview.id,
                    MockInterviewQuestion.intent.like("AI追问:%"),
                )
            )
        ).scalar_one())
        if follow_up_count < 2 and interview.question_count < 15:
            interview.question_count += 1
            db.add(MockInterviewQuestion(
                interview_id=interview.id,
                order_no=interview.question_count,
                question_type=question.question_type,
                question=evaluation.follow_up_question,
                intent=f"AI追问:{question.intent}",
                difficulty=question.difficulty,
                reference_points=question.reference_points,
                rubric=question.rubric,
                knowledge_chunk_ids=question.knowledge_chunk_ids,
                status="pending",
            ))
    interview.current_question_order = min(question.order_no + 1, interview.question_count)
    interview.token_usage = _merge_usage(interview.token_usage, state.get("token_usage"))
    await db.flush()
    next_question = await get_next_question(db, user_id=user_id, interview_id=interview_id)
    return {
        "evaluation": serialize_answer(answer),
        "next_question": next_question,
        "answered_count": await _answered_count(db, interview.id),
        "total_questions": interview.question_count,
    }


async def finish_mock_interview(
    db: AsyncSession, *, user_id: int, interview_id: int, agent_factory=MockInterviewAgent,
) -> dict:
    interview = await _get_owned_interview(db, user_id, interview_id)
    existing = (
        await db.execute(
            select(MockInterviewReport).where(MockInterviewReport.interview_id == interview.id)
        )
    ).scalar_one_or_none()
    if existing:
        return await get_mock_interview_report(db, user_id=user_id, interview_id=interview_id)
    questions = (
        await db.execute(
            select(MockInterviewQuestion)
            .where(MockInterviewQuestion.interview_id == interview.id)
            .order_by(MockInterviewQuestion.order_no)
        )
    ).scalars().all()
    answers = (
        await db.execute(
            select(MockInterviewAnswer)
            .join(MockInterviewQuestion, MockInterviewQuestion.id == MockInterviewAnswer.question_id)
            .where(MockInterviewQuestion.interview_id == interview.id)
        )
    ).scalars().all()
    if not answers:
        raise MockInterviewError("至少回答一道题后才能生成面试报告", 409)
    answer_map = {item.question_id: item for item in answers}
    reviews = [
        {
            "question": item.question,
            "answer": answer_map[item.id].answer_text,
            "score": answer_map[item.id].score,
            "dimension_scores": answer_map[item.id].dimension_scores,
            "feedback": answer_map[item.id].feedback,
        }
        for item in questions if item.id in answer_map
    ]
    overall = round(sum(item.score for item in answers) / len(answers))
    dimensions = _average_dimensions(answers)
    context = {
        "domain": interview.domain,
        "target_role": interview.target_role,
        "job_description": interview.job_description or "",
        "overall_score": overall,
        "dimension_scores": dimensions,
        "reviews": reviews,
        "weaknesses": [point for item in answers for point in item.missing_points][:20],
    }
    state = await agent_factory(domain=interview.domain).run(mode="report", context=context)
    generated = state["result"]
    report = MockInterviewReport(
        interview_id=interview.id,
        overall_score=overall,
        dimension_scores=dimensions,
        summary=generated.summary,
        strengths=generated.strengths,
        weaknesses=generated.weaknesses,
        improvement_plan_7_days=generated.improvement_plan_7_days,
        improvement_plan_30_days=generated.improvement_plan_30_days,
        model_name=state.get("used_model_name"),
        token_usage=state.get("token_usage"),
    )
    db.add(report)
    for item in generated.question_bank:
        db.add(MockInterviewQuestionRecommendation(
            interview_id=interview.id,
            weakness=item.weakness,
            question_type=item.question_type,
            question=item.question,
            difficulty=item.difficulty,
            reference_points=item.reference_points,
        ))
    interview.status = "completed"
    interview.overall_score = overall
    interview.completed_at = utc_now()
    interview.token_usage = _merge_usage(interview.token_usage, state.get("token_usage"))
    await db.flush()
    return await get_mock_interview_report(db, user_id=user_id, interview_id=interview_id)


async def get_mock_interview_report(db: AsyncSession, *, user_id: int, interview_id: int) -> dict:
    detail = await get_mock_interview(db, user_id=user_id, interview_id=interview_id)
    report = (
        await db.execute(
            select(MockInterviewReport).where(MockInterviewReport.interview_id == interview_id)
        )
    ).scalar_one_or_none()
    if not report:
        raise MockInterviewError("面试报告尚未生成", 404)
    recommendations = (
        await db.execute(
            select(MockInterviewQuestionRecommendation)
            .where(MockInterviewQuestionRecommendation.interview_id == interview_id)
            .order_by(MockInterviewQuestionRecommendation.id)
        )
    ).scalars().all()
    detail["report"] = serialize_report(report)
    detail["question_bank"] = [
        {
            "id": item.id, "weakness": item.weakness, "question_type": item.question_type,
            "question": item.question, "difficulty": item.difficulty,
            "reference_points": item.reference_points,
        }
        for item in recommendations
    ]
    return detail


async def retry_weaknesses(
    db: AsyncSession, *, user_id: int, interview_id: int, agent_factory=MockInterviewAgent,
) -> MockInterview:
    previous = await _get_owned_interview(db, user_id, interview_id)
    report = (
        await db.execute(
            select(MockInterviewReport).where(MockInterviewReport.interview_id == interview_id)
        )
    ).scalar_one_or_none()
    if not report:
        raise MockInterviewError("请先完成面试并生成报告", 409)
    request = MockInterviewCreateRequest(
        source_type="custom",
        resume_id=previous.resume_id,
        resume_source=previous.resume_source,
        resume_optimization_id=previous.resume_optimization_id,
        title=f"{previous.target_role}薄弱项复试",
        target_role=previous.target_role,
        company=previous.company,
        job_description=previous.job_description,
        difficulty=previous.difficulty,
        question_types=previous.question_types,
        question_count=max(3, min(8, previous.question_count)),
        focus_weaknesses=report.weaknesses,
    )
    return await create_mock_interview(
        db, user_id=user_id, request=request, agent_factory=agent_factory
    )


async def delete_mock_interview(db: AsyncSession, *, user_id: int, interview_id: int) -> None:
    interview = await _get_owned_interview(db, user_id, interview_id)
    await db.delete(interview)
    await db.flush()


async def _get_owned_interview(db: AsyncSession, user_id: int, interview_id: int) -> MockInterview:
    item = (
        await db.execute(
            select(MockInterview).where(
                MockInterview.id == interview_id, MockInterview.user_id == user_id
            )
        )
    ).scalar_one_or_none()
    if not item:
        raise MockInterviewError("面试记录不存在", 404)
    return item


async def _load_resume_text(
    db: AsyncSession, *, user_id: int, resume_id: int | None,
    resume_source: str, optimization_id: int | None,
) -> str:
    if resume_source == "optimized":
        version = (
            await db.execute(
                select(ResumeOptimizationVersion).where(
                    ResumeOptimizationVersion.id == optimization_id,
                    ResumeOptimizationVersion.user_id == user_id,
                )
            )
        ).scalar_one_or_none()
        if not version:
            raise MockInterviewError("优化简历版本不存在", 404)
        return version.optimized_content or ""
    if resume_id is None:
        return ""
    resume = (
        await db.execute(
            select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
        )
    ).scalar_one_or_none()
    if not resume:
        raise MockInterviewError("简历不存在", 404)
    return resume.extracted_text or ""


async def _answered_count(db: AsyncSession, interview_id: int) -> int:
    return int((
        await db.execute(
            select(func.count(MockInterviewAnswer.id))
            .join(MockInterviewQuestion, MockInterviewQuestion.id == MockInterviewAnswer.question_id)
            .where(MockInterviewQuestion.interview_id == interview_id)
        )
    ).scalar_one())


def serialize_interview(item: MockInterview) -> dict:
    return {
        "id": item.id, "title": item.title, "source_type": item.source_type,
        "job_id": item.job_id, "resume_id": item.resume_id,
        "target_role": item.target_role, "position": item.target_role,
        "company": item.company, "domain": item.domain, "difficulty": item.difficulty,
        "question_types": item.question_types, "question_count": item.question_count,
        "status": item.status, "current_question_order": item.current_question_order,
        "overall_score": item.overall_score, "score": item.overall_score,
        "created_at": item.created_at, "started_at": item.started_at,
        "completed_at": item.completed_at,
    }


def serialize_question(item: MockInterviewQuestion, answer: MockInterviewAnswer | None = None) -> dict:
    result = {
        "id": item.id, "order_no": item.order_no, "question_type": item.question_type,
        "type": item.question_type, "question": item.question, "difficulty": item.difficulty,
        "status": item.status, "duration_minutes": 5,
    }
    if answer:
        result.update({
            "answer": answer.answer_text, "duration_seconds": answer.duration_seconds,
            "score": answer.score, "dimension_scores": answer.dimension_scores,
            "matched_points": answer.matched_points, "missing_points": answer.missing_points,
            "feedback": answer.feedback, "follow_up_question": answer.follow_up_question,
        })
    return result


def serialize_answer(item: MockInterviewAnswer) -> dict:
    return {
        "question_id": item.question_id, "score": item.score,
        "dimension_scores": item.dimension_scores, "matched_points": item.matched_points,
        "missing_points": item.missing_points, "feedback": item.feedback,
        "follow_up_question": item.follow_up_question,
    }


def serialize_report(item: MockInterviewReport) -> dict:
    return {
        "id": item.id, "overall_score": item.overall_score,
        "dimension_scores": item.dimension_scores, "summary": item.summary,
        "strengths": item.strengths, "weaknesses": item.weaknesses,
        "improvement_plan_7_days": item.improvement_plan_7_days,
        "improvement_plan_30_days": item.improvement_plan_30_days,
    }


def _average_dimensions(answers: list[MockInterviewAnswer]) -> dict[str, int]:
    keys = {key for item in answers for key in item.dimension_scores}
    return {
        key: round(sum(int(item.dimension_scores.get(key, 0)) for item in answers) / len(answers))
        for key in keys
    }


def _merge_usage(current: dict | None, incoming: dict | None) -> dict:
    keys = {"prompt_tokens", "completion_tokens", "total_tokens"}
    return {key: int((current or {}).get(key, 0)) + int((incoming or {}).get(key, 0)) for key in keys}
