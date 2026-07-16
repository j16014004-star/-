"""Database helpers for career planning."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career_plan import CareerPlan, CareerPlanningProfile, CareerProjectAttachment


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
