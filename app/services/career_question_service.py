"""Asynchronous AI Q&A for career execution tasks."""
from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.career_question_agent import CareerQuestionAgent
from app.core.config import settings
from app.crud.ai_task import (
    claim_provider_call,
    count_active_tasks_for_user,
    create_ai_task,
    get_ai_task,
    update_ai_task,
)
from app.crud.career_plan import get_execution_by_id, get_owned_execution_task, get_plan
from app.crud.career_question import (
    create_question,
    get_latest_user_question,
    get_owned_question,
    get_question,
    get_reusable_question,
    get_task_questions,
)
from app.models.ai import AITask
from app.models.career_plan import CareerPlanQuestion
from app.models.user import User
from app.schemas.career_plan import CareerQuestionRequest
from app.services.career_plan_service import CareerPlanError, serialize_plan
from app.workers.process_launcher import WorkerLaunchError, launch_ai_task_worker


QUESTION_PROMPT_VERSION = "career-question-v1"


@dataclass(slots=True)
class CareerQuestionStartResult:
    task: AITask
    question: CareerPlanQuestion


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def serialize_question(question: CareerPlanQuestion) -> dict:
    return {
        "id": question.id,
        "execution_task_id": question.execution_task_id,
        "question": question.question,
        "answer": question.answer,
        "status": question.status,
        "error_message": question.error_message,
        "created_at": question.created_at,
        "answered_at": question.answered_at,
    }


async def submit_career_question(
    db: AsyncSession,
    *,
    user_id: int,
    execution_task_id: int,
    request: CareerQuestionRequest,
) -> CareerQuestionStartResult:
    # Serialize submissions per user to make concurrency and duplicate checks atomic.
    await db.execute(select(User.id).where(User.id == user_id).with_for_update())
    execution_task = await get_owned_execution_task(db, execution_task_id, user_id)
    if execution_task is None:
        raise CareerPlanError("执行任务不存在", 404)
    execution = await get_execution_by_id(db, execution_task.execution_plan_id, user_id)
    if execution is None:
        raise CareerPlanError("执行计划不存在", 404)
    plan = await get_plan(db, execution.career_plan_id, user_id)
    if plan is None:
        raise CareerPlanError("职业规划不存在", 404)

    safe_question, sensitive_redacted = redact_sensitive_text(request.question)
    input_hash = hashlib.sha256(
        f"{user_id}:{execution_task_id}:{safe_question}".encode("utf-8")
    ).hexdigest()
    reusable = await get_reusable_question(
        db,
        user_id=user_id,
        execution_task_id=execution_task_id,
        input_hash=input_hash,
    )
    if reusable is not None and reusable.ai_task_id:
        existing_task = await get_ai_task(db, reusable.ai_task_id)
        if existing_task is not None:
            return CareerQuestionStartResult(task=existing_task, question=reusable)

    if await count_active_tasks_for_user(db, user_id) >= settings.AI_MAX_CONCURRENT_TASKS:
        raise CareerPlanError("已有 AI 任务正在运行，请等待任务完成", 409)
    latest = await get_latest_user_question(db, user_id)
    now = utc_now_naive()
    if latest is not None and latest.created_at is not None:
        elapsed = (now - latest.created_at.replace(tzinfo=None)).total_seconds()
        if elapsed < settings.CAREER_QUESTION_COOLDOWN_SECONDS:
            raise CareerPlanError("提问过于频繁，请稍后再试", 429)

    question = CareerPlanQuestion(
        user_id=user_id,
        execution_task_id=execution_task_id,
        input_hash=input_hash,
        question=safe_question,
        status="pending",
        sensitive_redacted=sensitive_redacted,
        model_name=settings.CAREER_PLANNING_MODEL,
        prompt_version=QUESTION_PROMPT_VERSION,
    )
    await create_question(db, question)
    task = AITask(
        id=str(uuid.uuid4()),
        user_id=user_id,
        task_type="career_plan_question",
        resource_type="career_plan_question",
        resource_id=question.id,
        status="pending",
        progress=0,
        model_name=settings.CAREER_PLANNING_MODEL,
        prompt_version=QUESTION_PROMPT_VERSION,
        input_hash=input_hash,
        request_payload={
            "question_id": question.id,
            "execution_task_id": execution_task_id,
        },
    )
    await create_ai_task(db, task)
    question.ai_task_id = task.id
    await db.commit()
    try:
        launch_ai_task_worker(task.id)
    except WorkerLaunchError as exc:
        message = "无法启动职业规划答疑 worker，请稍后重试"
        task.status = "failed"
        task.progress = 100
        task.error_message = message
        task.finished_at = utc_now_naive()
        question.status = "failed"
        question.error_message = message
        await db.commit()
        raise CareerPlanError(message, 503) from exc
    return CareerQuestionStartResult(task=task, question=question)


async def list_career_questions(
    db: AsyncSession, *, user_id: int, execution_task_id: int
) -> list[dict]:
    task = await get_owned_execution_task(db, execution_task_id, user_id)
    if task is None:
        raise CareerPlanError("执行任务不存在", 404)
    return [
        serialize_question(item)
        for item in await get_task_questions(db, execution_task_id, user_id)
    ]


async def get_career_question_detail(
    db: AsyncSession, *, user_id: int, question_id: int
) -> dict:
    question = await get_owned_question(db, question_id, user_id)
    if question is None:
        raise CareerPlanError("答疑记录不存在", 404)
    return serialize_question(question)


async def execute_career_question_task(task_id: str) -> None:
    from app.core.database import async_session

    async with async_session() as db:
        task = await get_ai_task(db, task_id)
        if task is None or task.status != "pending":
            return
        question = await get_question(db, task.resource_id)
        if question is None:
            task.status = "failed"
            task.progress = 100
            task.error_message = "答疑记录不存在"
            task.finished_at = utc_now_naive()
            await db.commit()
            return
        if not settings.TENCENT_MAAS_API_KEY.strip():
            raise_error = CareerPlanError("未配置腾讯云 MaaS API Key", 503)
            await mark_career_question_failed(task_id, str(raise_error))
            raise raise_error
        task.status = "preparing"
        task.progress = 10
        task.started_at = utc_now_naive()
        question.status = "answering"
        question.error_message = None
        execution_task = await get_owned_execution_task(
            db, question.execution_task_id, question.user_id
        )
        if execution_task is None:
            raise_error = CareerPlanError("执行任务不存在", 404)
            await db.rollback()
            await mark_career_question_failed(task_id, str(raise_error))
            raise raise_error
        execution = await get_execution_by_id(
            db, execution_task.execution_plan_id, question.user_id
        )
        plan = (
            await get_plan(db, execution.career_plan_id, question.user_id)
            if execution is not None
            else None
        )
        if execution is None or plan is None:
            raise_error = CareerPlanError("职业规划执行上下文不存在", 404)
            await db.rollback()
            await mark_career_question_failed(task_id, str(raise_error))
            raise raise_error
        question_text = question.question
        sensitive_redacted = question.sensitive_redacted
        task_context = {
            "id": execution_task.id,
            "title": execution_task.title,
            "description": execution_task.description,
            "task_type": execution_task.task_type,
            "stage": execution_task.stage,
            "week_no": execution_task.week_no,
            "status": execution_task.status,
        }
        plan_context = serialize_plan(plan)
        await claim_provider_call(db, task, utc_now_naive())
        task.status = "generating"
        task.progress = 35
        await db.commit()

    try:
        state = await CareerQuestionAgent().run(
            question=question_text,
            task_context=task_context,
            plan_context=plan_context,
            sensitive_redacted=sensitive_redacted,
        )
        answer = state["result"].answer.strip()
        if sensitive_redacted:
            answer = "安全提示：你提交的内容包含疑似敏感值，系统已脱敏；请立即撤销或轮换相关凭据。\n\n" + answer
        usage = normalize_token_usage(state.get("token_usage") or {})
        chunks = state.get("knowledge_chunks") or []
        versions = sorted({chunk.version for chunk in chunks if chunk.version})

        async with async_session() as db:
            task = await get_ai_task(db, task_id)
            question = await get_question(db, task.resource_id) if task is not None else None
            if task is None or question is None:
                return
            task.status = "saving"
            task.progress = 90
            task.token_usage = usage
            used_model = state.get("used_model_name") or settings.CAREER_PLANNING_MODEL
            task.model_name = used_model or getattr(task, "model_name", None)
            question.model_name = used_model or getattr(question, "model_name", None)
            question.answer = answer
            question.status = "answered"
            question.error_message = None
            question.retrieval_source = state.get("retrieval_source") or "unknown"
            question.retrieval_error = state.get("retrieval_error")
            question.retrieved_chunk_ids = state.get("retrieved_chunk_ids") or []
            question.retrieval_audit = state.get("retrieval_audit") or []
            question.knowledge_base_version = ",".join(versions)[:100] or None
            question.answered_at = utc_now_naive()
            task.status = "success"
            task.progress = 100
            task.result_id = question.id
            task.error_message = None
            task.finished_at = utc_now_naive()
            await db.commit()
    except Exception as exc:
        await mark_career_question_failed(task_id, safe_question_error(exc))
        raise


async def mark_career_question_failed(task_id: str, message: str) -> None:
    from app.core.database import async_session

    async with async_session() as db:
        task = await get_ai_task(db, task_id)
        if task is None or task.status in ("success", "cancelled"):
            return
        await update_ai_task(
            db,
            task_id,
            status="failed",
            progress=100,
            error_message=message[:500],
            finished_at=utc_now_naive(),
        )
        question = await get_question(db, task.resource_id)
        if question is not None:
            question.status = "failed"
            question.error_message = message[:500]
        await db.commit()


def normalize_token_usage(raw_usage: dict) -> dict:
    prompt = int(raw_usage.get("prompt_tokens") or 0)
    completion = int(raw_usage.get("completion_tokens") or 0)
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": int(raw_usage.get("total_tokens") or prompt + completion),
        "usage_reported": bool(raw_usage),
    }


def redact_sensitive_text(text: str) -> tuple[str, bool]:
    redacted = text
    patterns = (
        (r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [已脱敏]"),
        (r"\bsk-[A-Za-z0-9_-]{8,}\b", "[已脱敏 API Key]"),
        (r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\b", "[已脱敏 Token]"),
        (
            r"(?i)\b(api[_ -]?key|access[_ -]?token|refresh[_ -]?token|password|passwd|secret)\b\s*[:=：]\s*[^\s,，;；]+",
            r"\1: [已脱敏]",
        ),
        (
            r"(密码|密钥|令牌)\s*(?:是|为|[:=：])\s*(?!什么|如何|怎么|多少|否)[^\s,，;；]+",
            r"\1：[已脱敏]",
        ),
    )
    for pattern, replacement in patterns:
        redacted = re.sub(pattern, replacement, redacted)
    return redacted, redacted != text


def safe_question_error(exc: Exception) -> str:
    if isinstance(exc, CareerPlanError):
        return str(exc)
    message = str(exc).strip()
    return message[:500] if message else "职业规划答疑失败，请稍后重试"
