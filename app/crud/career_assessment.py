"""Database helpers for stage progression and assessments."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career_plan import (
    CareerStageAssessment, CareerStageAssessmentAnswer,
    CareerStageAssessmentQuestion, CareerStageProgress,
)


async def get_stage_progresses(db: AsyncSession, execution_id: int, user_id: int):
    result = await db.execute(select(CareerStageProgress).where(
        CareerStageProgress.execution_plan_id == execution_id,
        CareerStageProgress.user_id == user_id,
    ).order_by(CareerStageProgress.stage_order))
    return list(result.scalars().all())


async def get_owned_assessment(db: AsyncSession, assessment_id: int, user_id: int):
    result = await db.execute(select(CareerStageAssessment).where(
        CareerStageAssessment.id == assessment_id,
        CareerStageAssessment.user_id == user_id,
    ))
    return result.scalar_one_or_none()


async def get_assessment(db: AsyncSession, assessment_id: int):
    return await db.get(CareerStageAssessment, assessment_id)


async def get_reusable_assessment(db: AsyncSession, execution_id: int, stage_order: int, user_id: int):
    result = await db.execute(select(CareerStageAssessment).where(
        CareerStageAssessment.execution_plan_id == execution_id,
        CareerStageAssessment.stage_order == stage_order,
        CareerStageAssessment.user_id == user_id,
        CareerStageAssessment.status.in_(("generating", "ready", "submitted", "evaluating")),
    ).order_by(CareerStageAssessment.created_at.desc()).limit(1))
    return result.scalar_one_or_none()


async def get_assessment_questions(db: AsyncSession, assessment_id: int):
    result = await db.execute(select(CareerStageAssessmentQuestion).where(
        CareerStageAssessmentQuestion.assessment_id == assessment_id
    ).order_by(CareerStageAssessmentQuestion.question_order))
    return list(result.scalars().all())


async def get_assessment_answers(db: AsyncSession, assessment_id: int):
    result = await db.execute(select(CareerStageAssessmentAnswer).where(
        CareerStageAssessmentAnswer.assessment_id == assessment_id
    ))
    return list(result.scalars().all())
