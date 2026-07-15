'''Resume optimization task orchestration and persistence.'''
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.resume_optimization_agent import ResumeOptimizationAgent
from app.core.config import settings
from app.crud.ai_task import (
    claim_provider_call,
    count_active_tasks_for_user,
    count_started_provider_calls,
    count_total_provider_tokens,
    create_ai_task,
    get_ai_task,
    get_reusable_task,
    update_ai_task,
)
from app.crud.resume import get_resume_by_id
from app.crud.resume_optimization import create_optimization_version
from app.models.ai import AITask, ResumeOptimizationVersion
from app.schemas.resume_optimization import ResumeOptimizationRequest
from app.workers.process_launcher import WorkerLaunchError, launch_ai_task_worker


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ResumeOptimizationError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(slots=True)
class StartOptimizationResult:
    task: AITask
    created: bool


def build_input_hash(
    *,
    user_id: int,
    resume_id: int,
    resume_text: str,
    payload: dict,
) -> str:
    source = {
        'user_id': user_id,
        'resume_id': resume_id,
        'resume_hash': hashlib.sha256(resume_text.encode('utf-8')).hexdigest(),
        'payload': payload,
        'prompt_version': settings.AI_PROMPT_VERSION,
    }
    serialized = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


async def start_resume_optimization(
    db: AsyncSession,
    *,
    user_id: int,
    resume_id: int,
    request: ResumeOptimizationRequest,
) -> StartOptimizationResult:
    resume = await get_resume_by_id(db, resume_id, user_id)
    if resume is None:
        raise ResumeOptimizationError('简历不存在', 404)
    if resume.status != 'completed':
        raise ResumeOptimizationError('简历尚未解析完成，暂时不能优化', 409)
    resume_text = (resume.extracted_text or '').strip()
    if not resume_text:
        raise ResumeOptimizationError('简历没有可优化的文本内容', 422)

    request_payload = request.model_dump(mode='json')
    input_hash = build_input_hash(
        user_id=user_id,
        resume_id=resume_id,
        resume_text=resume_text,
        payload=request_payload,
    )
    existing = await get_reusable_task(
        db,
        user_id=user_id,
        resource_id=resume_id,
        input_hash=input_hash,
    )
    if existing is not None:
        return StartOptimizationResult(existing, created=False)

    active_count = await count_active_tasks_for_user(db, user_id)
    if active_count >= settings.AI_MAX_CONCURRENT_TASKS:
        raise ResumeOptimizationError('已有 AI 任务正在运行，请等待任务完成', 409)

    task = AITask(
        id=str(uuid4()),
        user_id=user_id,
        task_type='resume_optimization',
        resource_type='resume',
        resource_id=resume_id,
        status='pending',
        progress=0,
        model_name=settings.RESUME_OPTIMIZATION_MODEL,
        prompt_version=settings.AI_PROMPT_VERSION,
        input_hash=input_hash,
        request_payload=request_payload,
    )
    await create_ai_task(db, task)
    try:
        launch_ai_task_worker(task.id)
    except WorkerLaunchError as exc:
        task.status = 'failed'
        task.progress = 100
        task.error_message = '无法启动简历优化 worker，请稍后重试'
        task.finished_at = utc_now_naive()
        await db.flush()
        raise ResumeOptimizationError(task.error_message, 503) from exc
    return StartOptimizationResult(task, created=True)


async def execute_resume_optimization_task(task_id: str) -> None:
    from app.core.database import async_session

    async with async_session() as db:
        task = await get_ai_task(db, task_id)
        if task is None or task.status != 'pending':
            return
        task.status = 'preparing'
        task.progress = 10
        task.started_at = utc_now_naive()
        await db.commit()

    try:
        async with async_session() as db:
            task = await get_ai_task(db, task_id)
            if task is None:
                return
            resume = await get_resume_by_id(db, task.resource_id, task.user_id)
            if resume is None or resume.status != 'completed' or not (resume.extracted_text or '').strip():
                raise ResumeOptimizationError('简历不存在或尚未解析完成', 422)
            resume_text = (resume.extracted_text or '').strip()[:settings.AI_MAX_RESUME_CHARS]
            structured_data = resume.structured_data
            request_payload = task.request_payload or {}

            if not settings.TENCENT_MAAS_API_KEY.strip():
                raise ResumeOptimizationError('未配置腾讯云 MaaS API Key', 503)
            max_output_tokens = settings.AI_MAX_OUTPUT_TOKENS
            if settings.AI_TEST_MODE:
                used_calls = await count_started_provider_calls(db, exclude_task_id=task.id)
                if used_calls >= settings.AI_TEST_MAX_LIVE_CALLS:
                    raise ResumeOptimizationError('测试模式的真实模型调用额度已用完', 429)
                used_tokens = await count_total_provider_tokens(db, exclude_task_id=task.id)
                remaining_tokens = settings.AI_TEST_MAX_TOTAL_TOKENS - used_tokens
                if remaining_tokens <= 0:
                    raise ResumeOptimizationError('测试模式的 AI token 总用量已达到上限', 429)
                max_output_tokens = max(1, min(settings.AI_MAX_OUTPUT_TOKENS, remaining_tokens))
            await claim_provider_call(db, task, utc_now_naive())
            task.status = 'generating'
            task.progress = 30
            await db.commit()

        agent = ResumeOptimizationAgent()
        state = await agent.run(
            resume_text=resume_text,
            structured_data=structured_data,
            request_payload=request_payload,
            max_output_tokens=max_output_tokens,
        )

        async with async_session() as db:
            task = await get_ai_task(db, task_id)
            if task is None:
                return
            task.status = 'validating'
            task.progress = 75
            task.token_usage = state.get('token_usage') or {}
            await db.commit()

        result = state['result']
        chunks = state.get('knowledge_chunks') or []
        resume_hash = hashlib.sha256(resume_text.encode('utf-8')).hexdigest()
        knowledge_versions = sorted({chunk.version for chunk in chunks if chunk.version})
        kb_version = hashlib.sha256('|'.join(knowledge_versions).encode('utf-8')).hexdigest()[:16] if knowledge_versions else None

        async with async_session() as db:
            task = await get_ai_task(db, task_id)
            if task is None:
                return
            task.status = 'saving'
            task.progress = 90
            await db.flush()
            version = ResumeOptimizationVersion(
                user_id=task.user_id,
                resume_id=task.resource_id,
                task_id=task.id,
                analysis_id=request_payload.get('analysis_id'),
                optimization_type=request_payload.get('optimization_type', 'general'),
                target_role=request_payload.get('target_role'),
                optimization_focus=request_payload.get('optimization_focus') or ['all'],
                style=request_payload.get('style', 'professional'),
                preserve_structure=bool(request_payload.get('preserve_structure', True)),
                optimization_summary=result.optimization_summary,
                original_content=resume_text,
                optimized_content=result.optimized_content,
                change_items=[item.model_dump(mode='json') for item in result.change_items],
                confirmation_questions=result.confirmation_questions,
                confirmation_actions=[],
                score_improvement=result.score_improvement,
                knowledge_base_version=kb_version,
                retrieved_chunk_ids=[chunk.id for chunk in chunks],
                model_name=settings.RESUME_OPTIMIZATION_MODEL,
                embedding_model=(settings.TENCENT_MAAS_EMBEDDING_MODEL if settings.QDRANT_ENABLED else None),
                prompt_version=settings.AI_PROMPT_VERSION,
                resume_content_hash=resume_hash,
            )
            await create_optimization_version(db, version)
            task.status = 'success'
            task.progress = 100
            task.result_id = version.id
            task.error_message = None
            task.finished_at = utc_now_naive()
            await db.commit()
    except Exception as exc:
        await mark_task_failed(task_id, _safe_error_message(exc))
        raise


async def mark_task_failed(task_id: str, message: str) -> None:
    from app.core.database import async_session

    async with async_session() as db:
        task = await get_ai_task(db, task_id)
        if task is None or task.status in ('success', 'cancelled'):
            return
        await update_ai_task(
            db,
            task_id,
            status='failed',
            progress=100,
            error_message=message[:500],
            finished_at=utc_now_naive(),
        )
        await db.commit()


def _safe_error_message(exc: Exception) -> str:
    if isinstance(exc, ResumeOptimizationError):
        return str(exc)
    message = str(exc).strip()
    allowed = (
        '未配置腾讯云', '测试模式', 'AI 返回', '优化结果', '修改项',
        '腾讯云模型', 'Embedding',
    )
    if any(message.startswith(prefix) for prefix in allowed):
        return message[:500]
    return '简历优化任务执行失败，请稍后重试'
