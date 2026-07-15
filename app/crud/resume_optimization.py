'''Database access for resume optimization versions.'''
from sqlalchemy import func, select
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


async def list_saved_optimization_versions(
    db: AsyncSession,
    *,
    user_id: int,
    page: int,
    page_size: int,
) -> tuple[list[ResumeOptimizationVersion], int]:
    total_result = await db.execute(
        select(func.count()).select_from(ResumeOptimizationVersion).where(
            ResumeOptimizationVersion.user_id == user_id,
            ResumeOptimizationVersion.is_saved.is_(True),
        )
    )
    total = int(total_result.scalar_one() or 0)
    result = await db.execute(
        select(ResumeOptimizationVersion)
        .where(
            ResumeOptimizationVersion.user_id == user_id,
            ResumeOptimizationVersion.is_saved.is_(True),
        )
        .order_by(ResumeOptimizationVersion.saved_at.desc(), ResumeOptimizationVersion.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_owned_saved_optimization_version(
    db: AsyncSession,
    *,
    optimization_id: int,
    user_id: int,
) -> ResumeOptimizationVersion | None:
    result = await db.execute(
        select(ResumeOptimizationVersion).where(
            ResumeOptimizationVersion.id == optimization_id,
            ResumeOptimizationVersion.user_id == user_id,
            ResumeOptimizationVersion.is_saved.is_(True),
        )
    )
    return result.scalar_one_or_none()
