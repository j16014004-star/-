"""Database helpers for career planning."""
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career_plan import (
    CareerPlan,
    CareerPlanCheckin,
    CareerPlanExecution,
    CareerPlanExecutionTask,
    CareerPlanningProfile,
    CareerProjectAttachment,
)


async def create_project_attachment(
    db: AsyncSession,
    attachment: CareerProjectAttachment,
) -> CareerProjectAttachment:
    db.add(attachment)
    await db.flush()
    return attachment


async def get_project_attachment(
    db: AsyncSession,
    attachment_id: int,
    user_id: int,
) -> CareerProjectAttachment | None:
    result = await db.execute(
        select(CareerProjectAttachment).where(
            CareerProjectAttachment.id == attachment_id,
            CareerProjectAttachment.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_project_attachments(
    db: AsyncSession,
    attachment_ids: list[int],
    user_id: int,
) -> list[CareerProjectAttachment]:
    if not attachment_ids:
        return []
    result = await db.execute(
        select(CareerProjectAttachment).where(
            CareerProjectAttachment.id.in_(attachment_ids),
            CareerProjectAttachment.user_id == user_id,
        )
    )
    return list(result.scalars().all())


async def delete_project_attachment(
    db: AsyncSession,
    attachment: CareerProjectAttachment,
) -> None:
    await db.delete(attachment)
    await db.flush()


async def create_profile(
    db: AsyncSession,
    profile: CareerPlanningProfile,
) -> CareerPlanningProfile:
    db.add(profile)
    await db.flush()
    return profile


async def get_profile(
    db: AsyncSession,
    profile_id: int,
    user_id: int,
) -> CareerPlanningProfile | None:
    result = await db.execute(
        select(CareerPlanningProfile).where(
            CareerPlanningProfile.id == profile_id,
            CareerPlanningProfile.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def create_plan(db: AsyncSession, plan: CareerPlan) -> CareerPlan:
    db.add(plan)
    await db.flush()
    return plan


async def get_plan(
    db: AsyncSession,
    plan_id: int,
    user_id: int,
) -> CareerPlan | None:
    result = await db.execute(
        select(CareerPlan).where(CareerPlan.id == plan_id, CareerPlan.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_plan_by_task(
    db: AsyncSession,
    task_id: str,
) -> CareerPlan | None:
    result = await db.execute(select(CareerPlan).where(CareerPlan.task_id == task_id))
    return result.scalar_one_or_none()


async def get_execution_by_plan(
    db: AsyncSession, plan_id: int, user_id: int
) -> CareerPlanExecution | None:
    result = await db.execute(
        select(CareerPlanExecution).where(
            CareerPlanExecution.career_plan_id == plan_id,
            CareerPlanExecution.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_current_execution(
    db: AsyncSession, user_id: int
) -> CareerPlanExecution | None:
    result = await db.execute(
        select(CareerPlanExecution)
        .where(
            CareerPlanExecution.user_id == user_id,
            CareerPlanExecution.status == "active",
        )
        .order_by(CareerPlanExecution.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def pause_active_executions(db: AsyncSession, user_id: int) -> None:
    await db.execute(
        update(CareerPlanExecution)
        .where(
            CareerPlanExecution.user_id == user_id,
            CareerPlanExecution.status == "active",
        )
        .values(status="paused")
    )


async def create_execution(
    db: AsyncSession, execution: CareerPlanExecution
) -> CareerPlanExecution:
    db.add(execution)
    await db.flush()
    return execution


async def create_execution_tasks(
    db: AsyncSession, tasks: list[CareerPlanExecutionTask]
) -> list[CareerPlanExecutionTask]:
    db.add_all(tasks)
    await db.flush()
    return tasks


async def get_execution_tasks(
    db: AsyncSession, execution_id: int, user_id: int
) -> list[CareerPlanExecutionTask]:
    result = await db.execute(
        select(CareerPlanExecutionTask)
        .where(
            CareerPlanExecutionTask.execution_plan_id == execution_id,
            CareerPlanExecutionTask.user_id == user_id,
        )
        .order_by(
            CareerPlanExecutionTask.week_no,
            CareerPlanExecutionTask.planned_date,
            CareerPlanExecutionTask.id,
        )
    )
    return list(result.scalars().all())


async def get_owned_execution_task(
    db: AsyncSession, task_id: int, user_id: int
) -> CareerPlanExecutionTask | None:
    result = await db.execute(
        select(CareerPlanExecutionTask).where(
            CareerPlanExecutionTask.id == task_id,
            CareerPlanExecutionTask.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_execution_by_id(
    db: AsyncSession, execution_id: int, user_id: int
) -> CareerPlanExecution | None:
    result = await db.execute(
        select(CareerPlanExecution).where(
            CareerPlanExecution.id == execution_id,
            CareerPlanExecution.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def create_checkin(db: AsyncSession, checkin: CareerPlanCheckin) -> CareerPlanCheckin:
    db.add(checkin)
    await db.flush()
    return checkin


async def get_recent_checkins(
    db: AsyncSession, execution_id: int, user_id: int, limit: int = 10
) -> list[tuple[CareerPlanCheckin, str]]:
    result = await db.execute(
        select(CareerPlanCheckin, CareerPlanExecutionTask.title)
        .join(
            CareerPlanExecutionTask,
            CareerPlanExecutionTask.id == CareerPlanCheckin.task_id,
        )
        .where(
            CareerPlanCheckin.user_id == user_id,
            CareerPlanExecutionTask.execution_plan_id == execution_id,
        )
        .order_by(CareerPlanCheckin.checked_in_at.desc())
        .limit(limit)
    )
    return list(result.all())
