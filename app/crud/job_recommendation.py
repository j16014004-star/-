"""岗位推荐会话、任务与结果 CRUD"""
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobPlatformLoginSession, JobRecommendResult, JobRecommendTask


async def create_login_session(
    db: AsyncSession,
    session: JobPlatformLoginSession,
) -> JobPlatformLoginSession:
    db.add(session)
    await db.flush()
    return session


async def get_login_session(
    db: AsyncSession, session_id: str, user_id: int
) -> JobPlatformLoginSession | None:
    result = await db.execute(
        select(JobPlatformLoginSession).where(
            JobPlatformLoginSession.id == session_id,
            JobPlatformLoginSession.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_latest_login_session(
    db: AsyncSession, user_id: int, source: str
) -> JobPlatformLoginSession | None:
    result = await db.execute(
        select(JobPlatformLoginSession)
        .where(
            JobPlatformLoginSession.user_id == user_id,
            JobPlatformLoginSession.source == source,
        )
        .order_by(JobPlatformLoginSession.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_recommend_task(
    db: AsyncSession, task: JobRecommendTask
) -> JobRecommendTask:
    db.add(task)
    await db.flush()
    return task


async def get_recommend_task(
    db: AsyncSession, task_id: str, user_id: int
) -> JobRecommendTask | None:
    result = await db.execute(
        select(JobRecommendTask).where(
            JobRecommendTask.id == task_id,
            JobRecommendTask.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_active_recommend_task(
    db: AsyncSession, user_id: int, source: str
) -> JobRecommendTask | None:
    result = await db.execute(
        select(JobRecommendTask).where(
            JobRecommendTask.user_id == user_id,
            JobRecommendTask.source == source,
            JobRecommendTask.status.in_(("pending", "crawling", "matching")),
        )
    )
    return result.scalar_one_or_none()


async def get_latest_recommend_task_by_login_session(
    db: AsyncSession, login_session_id: str, user_id: int
) -> JobRecommendTask | None:
    result = await db.execute(
        select(JobRecommendTask)
        .where(
            JobRecommendTask.login_session_id == login_session_id,
            JobRecommendTask.user_id == user_id,
        )
        .order_by(JobRecommendTask.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def update_task(
    db: AsyncSession, task_id: str, **values
) -> JobRecommendTask | None:
    result = await db.execute(select(JobRecommendTask).where(JobRecommendTask.id == task_id))
    task = result.scalar_one_or_none()
    if task:
        for key, value in values.items():
            setattr(task, key, value)
        await db.flush()
    return task


async def create_recommend_result(
    db: AsyncSession, result_item: JobRecommendResult
) -> JobRecommendResult:
    db.add(result_item)
    await db.flush()
    return result_item


async def get_task_results(
    db: AsyncSession, task_id: str, user_id: int, page: int, page_size: int
) -> tuple[list[tuple[JobRecommendResult, Job]], int]:
    base = (
        select(JobRecommendResult, Job)
        .join(Job, Job.id == JobRecommendResult.job_id)
        .where(
            JobRecommendResult.task_id == task_id,
            JobRecommendResult.user_id == user_id,
        )
    )
    count_query = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    query = (
        base.order_by(
            JobRecommendResult.matched_skill_count.desc(),
            JobRecommendResult.match_score.desc(),
            Job.crawl_time.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list((await db.execute(query)).all()), total
