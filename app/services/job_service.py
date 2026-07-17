"""
岗位业务逻辑
"""
import re

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.job import (
    create_application,
    get_job_by_id,
    get_jobs,
)
from app.crud.resume import get_resume_by_id
from app.models.job import Job


# 技能关键词表（用于从纯文本中提取）
_SKILL_KEYWORDS = [
    "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#",
    "PHP", "Ruby", "Swift", "Kotlin", "Scala",
    "FastAPI", "Flask", "Django", "Spring", "Vue", "React", "Angular",
    "MySQL", "Redis", "MongoDB", "PostgreSQL", "Elasticsearch",
    "Docker", "Kubernetes", "Git", "Linux", "Nginx",
    "Node.js", "Express", "jQuery", "HTML", "CSS",
    "SQLAlchemy", "Alembic", "Pydantic", "JWT", "OAuth",
    "RESTful", "API", "WebSocket", "Celery", "RabbitMQ", "Kafka",
    "TensorFlow", "PyTorch", "scikit-learn", "pandas", "NumPy",
    "AWS", "Azure", "GCP",
    "Hadoop", "Spark", "Flink",
    "Excel", "Word", "PowerPoint",
]


def _extract_skills_from_text(text: str) -> list[str]:
    """从纯文本中提取技能关键词"""
    found = []
    seen = set()
    text_lower = text.lower()
    for kw in _SKILL_KEYWORDS:
        if kw.lower() in text_lower and kw.lower() not in seen:
            seen.add(kw.lower())
            found.append(kw)
    return found


async def get_recommendations(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    city: str | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
    source: str | None = None,
) -> dict:
    """获取岗位推荐列表"""
    jobs, total = await get_jobs(
        db=db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        city=city,
        salary_min=salary_min,
        salary_max=salary_max,
        source=source,
    )
    return {
        "items": jobs,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def recommend_jobs_by_resume(
    db: AsyncSession,
    resume_id: int,
    user_id: int,
) -> dict:
    """
    根据简历技能匹配推荐岗位

    1. 获取简历的结构化数据中的技能列表
    2. 检索所有活跃岗位
    3. 按技能重叠数匹配、排序、打分
    """
    # ── 获取简历并校验所有权 ──
    resume = await get_resume_by_id(db, resume_id, user_id)
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在或不属于当前用户")

    # ── 提取简历技能 ──
    resume_skills = []
    if resume.structured_data:
        resume_skills = resume.structured_data.get("skills", []) or []

    if not resume_skills:
        # 如果结构化数据没有技能，尝试从 extracted_text 里提取
        if resume.extracted_text:
            resume_skills = _extract_skills_from_text(resume.extracted_text)

    if not resume_skills:
        return {"items": [], "total": 0, "page": 1, "page_size": 20}

    # ── 获取所有活跃岗位 ──
    result = await db.execute(select(Job).where(Job.is_active == True))
    all_jobs = list(result.scalars().all())

    if not all_jobs:
        return {"items": [], "total": 0, "page": 1, "page_size": 20}

    # ── 技能匹配 ──
    resume_skill_set = set(s.lower().strip() for s in resume_skills if s)
    total_skills = len(resume_skill_set)

    scored: list[tuple[Job, int, list[str]]] = []
    for job in all_jobs:
        job_skills = job.skills or []
        job_skill_set = set(s.lower().strip() for s in job_skills if s)

        matched = resume_skill_set & job_skill_set
        if matched:
            match_count = len(matched)
            matched_skills = [s for s in job_skills if s.lower().strip() in resume_skill_set]
            scored.append((job, match_count, matched_skills))

    # ── 排序 ──
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:20]

    # ── 组合结果 ──
    items = []
    for job, match_count, matched_skills in top:
        score = int((match_count / total_skills) * 100) if total_skills else 0
        items.append({
            "id": job.id,
            "company": job.company,
            "company_logo": job.company_logo,
            "title": job.title,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "city": job.city,
            "experience_required": job.experience_required,
            "education_required": job.education_required,
            "skills": job.skills or [],
            "description": None,
            "match_score": score,
            "match_reasons": [f"技能匹配度 {score}%"] + [f"匹配: {s}" for s in matched_skills[:5]],
            "source": job.source,
            "source_name": job.source_name,
            "source_url": job.source_url,
            "is_active": job.is_active,
            "crawl_time": job.crawl_time,
            "created_at": job.created_at,
        })

    return {
        "items": items,
        "total": len(items),
        "page": 1,
        "page_size": 20,
    }


async def get_job_detail(db: AsyncSession, job_id: int) -> Job:
    """获取岗位详情"""
    job = await get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")
    return job


async def apply_job(
    db: AsyncSession,
    user_id: int,
    job_id: int,
    resume_id: int,
    cover_letter: str | None = None,
    resume_source: str = "original",
    resume_optimization_id: int | None = None,
) -> dict:
    """投递岗位"""
    # 校验岗位存在
    job = await get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    # 校验简历属于当前用户
    resume = await get_resume_by_id(db, resume_id, user_id)
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在或不属于当前用户")

    if resume_source == "optimized":
        from app.crud.resume_optimization import get_owned_saved_optimization_version
        version = await get_owned_saved_optimization_version(
            db, optimization_id=resume_optimization_id, user_id=user_id,
        ) if resume_optimization_id else None
        if not version or version.resume_id != resume_id:
            raise HTTPException(status_code=404, detail="优化简历不存在、未保存或不属于当前原始简历")
    elif resume_source != "original" or resume_optimization_id is not None:
        raise HTTPException(status_code=422, detail="简历来源参数无效")

    # 创建投递
    app = await create_application(
        db, user_id, job_id, resume_id, cover_letter,
        resume_source, resume_optimization_id,
    )
    return {
        "id": app.id,
        "job_id": app.job_id,
        "resume_id": app.resume_id,
        "resume_source": app.resume_source,
        "resume_optimization_id": app.resume_optimization_id,
        "status": app.status,
        "apply_type": app.apply_type,
        "applied_at": app.applied_at,
        "agent_task_id": None,
    }
