"""Database access for career execution task AI questions."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career_plan import CareerPlanQuestion


async def create_question(
    db: AsyncSession, question: CareerPlanQuestion
) -> CareerPlanQuestion:
    db.add(question)
    await db.flush()
    return question


async def get_question(db: AsyncSession, question_id: int) -> CareerPlanQuestion | None:
    result = await db.execute(
        select(CareerPlanQuestion).where(CareerPlanQuestion.id == question_id)
    )
    return result.scalar_one_or_none()


async def get_owned_question(
    db: AsyncSession, question_id: int, user_id: int
) -> CareerPlanQuestion | None:
    result = await db.execute(
        select(CareerPlanQuestion).where(
            CareerPlanQuestion.id == question_id,
            CareerPlanQuestion.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_task_questions(
    db: AsyncSession, execution_task_id: int, user_id: int
) -> list[CareerPlanQuestion]:
    result = await db.execute(
        select(CareerPlanQuestion)
        .where(
            CareerPlanQuestion.execution_task_id == execution_task_id,
            CareerPlanQuestion.user_id == user_id,
        )
        .order_by(CareerPlanQuestion.created_at.desc())
    )
    return list(result.scalars().all())


async def get_reusable_question(
    db: AsyncSession, *, user_id: int, execution_task_id: int, input_hash: str
) -> CareerPlanQuestion | None:
    result = await db.execute(
        select(CareerPlanQuestion)
        .where(
            CareerPlanQuestion.user_id == user_id,
            CareerPlanQuestion.execution_task_id == execution_task_id,
            CareerPlanQuestion.input_hash == input_hash,
        )
        .order_by(CareerPlanQuestion.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_latest_user_question(
    db: AsyncSession, user_id: int
) -> CareerPlanQuestion | None:
    result = await db.execute(
        select(CareerPlanQuestion)
        .where(CareerPlanQuestion.user_id == user_id)
        .order_by(CareerPlanQuestion.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
