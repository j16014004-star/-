"""
岗位 CRUD 操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.models.job import Job, JobApplication


async def get_job_by_source(
    db: AsyncSession, source: str, source_id: str
) -> Job | None:
    """按来源平台+ID 查询岗位（去重用）"""
    result = await db.execute(
        select(Job).where(Job.source == source, Job.source_id == source_id)
    )
    return result.scalar_one_or_none()


async def upsert_job(db: AsyncSession, data: dict) -> Job:
    """新增或更新岗位"""
    existing = await get_job_by_source(db, data["source"], data["source_id"])
    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
        await db.flush()
        await db.refresh(existing)
        return existing
    job = Job(**data)
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


async def bulk_save_jobs(db: AsyncSession, jobs_data: list[dict]) -> int:
    """批量保存岗位，返回新增+更新数量"""
    count = 0
    for data in jobs_data:
        await upsert_job(db, data)
        count += 1
    return count


async def get_jobs(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    city: str | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
    source: str | None = None,
) -> tuple[list[Job], int]:
    """分页查询岗位列表"""
    query = select(Job).where(Job.is_active == True)

    if keyword:
        kw = f"%{keyword}%"
        query = query.where(
            or_(Job.title.ilike(kw), Job.company.ilike(kw), Job.skills.ilike(kw))
        )
    if city:
        query = query.where(Job.city == city)
    if salary_min is not None:
        query = query.where(Job.salary_max >= salary_min)
    if salary_max is not None:
        query = query.where(Job.salary_min <= salary_max)
    if source:
        query = query.where(Job.source == source)

    # 总数
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # 分页
    offset = (page - 1) * page_size
    query = query.order_by(Job.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_job_by_id(db: AsyncSession, job_id: int) -> Job | None:
    """按ID获取岗位详情"""
    result = await db.execute(select(Job).where(Job.id == job_id))
    return result.scalar_one_or_none()


async def create_application(
    db: AsyncSession,
    user_id: int,
    job_id: int,
    resume_id: int,
    cover_letter: str | None = None,
) -> JobApplication:
    """创建投递记录"""
    app = JobApplication(
        user_id=user_id,
        job_id=job_id,
        resume_id=resume_id,
        cover_letter=cover_letter,
    )
    db.add(app)
    await db.flush()
    await db.refresh(app)
    return app


async def get_user_applications(
    db: AsyncSession, user_id: int
) -> list[JobApplication]:
    """获取用户投递列表"""
    result = await db.execute(
        select(JobApplication)
        .where(JobApplication.user_id == user_id)
        .order_by(JobApplication.created_at.desc())
    )
    return list(result.scalars().all())
