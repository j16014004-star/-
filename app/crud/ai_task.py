'''Database access for generic AI tasks.'''
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AITask


ACTIVE_STATUSES = ('pending', 'preparing', 'generating', 'validating', 'saving')


async def create_ai_task(db: AsyncSession, task: AITask) -> AITask:
    db.add(task)
    await db.flush()
    return task


async def get_ai_task(db: AsyncSession, task_id: str) -> AITask | None:
    result = await db.execute(select(AITask).where(AITask.id == task_id))
    return result.scalar_one_or_none()


async def get_owned_ai_task(db: AsyncSession, task_id: str, user_id: int) -> AITask | None:
    result = await db.execute(
        select(AITask).where(AITask.id == task_id, AITask.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_reusable_task(
    db: AsyncSession,
    *,
    user_id: int,
    resource_id: int,
    input_hash: str,
) -> AITask | None:
    result = await db.execute(
        select(AITask)
        .where(
            AITask.user_id == user_id,
            AITask.task_type == 'resume_optimization',
            AITask.resource_id == resource_id,
            AITask.input_hash == input_hash,
            AITask.status.in_((*ACTIVE_STATUSES, 'success')),
        )
        .order_by(AITask.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def count_active_tasks_for_user(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        select(func.count(AITask.id)).where(
            AITask.user_id == user_id,
            AITask.status.in_(ACTIVE_STATUSES),
        )
    )
    return int(result.scalar() or 0)


async def count_started_provider_calls(db: AsyncSession, *, exclude_task_id: str) -> int:
    result = await db.execute(
        select(func.count(AITask.id)).where(
            AITask.task_type == 'resume_optimization',
            AITask.provider_call_started_at.is_not(None),
            AITask.id != exclude_task_id,
        )
    )
    return int(result.scalar() or 0)


async def count_total_provider_tokens(db: AsyncSession, *, exclude_task_id: str | None = None) -> int:
    query = select(AITask.token_usage).where(
        AITask.task_type == 'resume_optimization',
        AITask.token_usage.is_not(None),
    )
    if exclude_task_id is not None:
        query = query.where(AITask.id != exclude_task_id)
    result = await db.execute(query)
    total = 0
    for usage in result.scalars().all():
        if not isinstance(usage, dict):
            continue
        try:
            total += int(usage.get('total_tokens') or 0)
        except (TypeError, ValueError):
            continue
    return total


async def update_ai_task(db: AsyncSession, task_id: str, **values) -> AITask | None:
    task = await get_ai_task(db, task_id)
    if task is None:
        return None
    for key, value in values.items():
        setattr(task, key, value)
    await db.flush()
    return task


async def claim_provider_call(db: AsyncSession, task: AITask, now: datetime) -> None:
    task.provider_call_started_at = now
    await db.flush()
