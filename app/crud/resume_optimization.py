'''Database access for resume optimization versions.'''
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import ResumeOptimizationVersion


async def create_optimization_version(
    db: AsyncSession,
    version: ResumeOptimizationVersion,
) -> ResumeOptimizationVersion:
    db.add(version)
    await db.flush()
    return version


async def get_owned_optimization_version(
    db: AsyncSession,
    *,
    optimization_id: int,
    resume_id: int,
    user_id: int,
) -> ResumeOptimizationVersion | None:
    result = await db.execute(
        select(ResumeOptimizationVersion).where(
            ResumeOptimizationVersion.id == optimization_id,
            ResumeOptimizationVersion.resume_id == resume_id,
            ResumeOptimizationVersion.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()
