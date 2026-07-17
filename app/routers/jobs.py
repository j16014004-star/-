"""
岗位路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.job import JobApplyRequest
from app.services.job_service import (
    apply_job, get_job_detail, get_recommendations, recommend_jobs_by_resume,
)

router = APIRouter(prefix="/api/jobs", tags=["岗位"])


def job_to_dict(job, detail: bool = False) -> dict:
    """序列化岗位对象"""
    d = {
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
        "description": job.description if detail else None,
        "match_score": job.match_score,
        "match_reasons": job.match_reasons,
        "source": job.source,
        "source_name": job.source_name,
        "source_url": job.source_url,
        "is_active": job.is_active,
        "crawl_time": job.crawl_time,
        "created_at": job.created_at,
    }
    if detail:
        d["area"] = job.area
    return d


@router.get("/recommendations")
async def list_jobs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: str | None = Query(None, description="搜索关键词"),
    city: str | None = Query(None, description="城市"),
    salary_min: int | None = Query(None, ge=0, description="最低薪资"),
    salary_max: int | None = Query(None, ge=0, description="最高薪资"),
    source: str | None = Query(None, description="来源: 58/boss/lagou/liepin"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取推荐岗位列表"""
    result = await get_recommendations(
        db=db, page=page, page_size=page_size,
        keyword=keyword, city=city,
        salary_min=salary_min, salary_max=salary_max,
        source=source,
    )
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [job_to_dict(j) for j in result["items"]],
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
        },
    }


@router.post("/recommend")
async def recommend_jobs(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """根据简历技能推荐岗位"""
    resume_id = body.get("resume_id")
    if not resume_id:
        raise HTTPException(status_code=400, detail="缺少 resume_id")

    result = await recommend_jobs_by_resume(
        db=db, resume_id=resume_id, user_id=current_user.id,
    )
    return {
        "code": 200,
        "message": "success",
        "data": result,
    }


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取岗位详情"""
    job = await get_job_detail(db, job_id)
    return {
        "code": 200,
        "message": "success",
        "data": job_to_dict(job, detail=True),
    }


@router.post("/{job_id}/apply")
async def apply_to_job(
    job_id: int,
    body: JobApplyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """投递岗位"""
    result = await apply_job(
        db=db,
        user_id=current_user.id,
        job_id=job_id,
        resume_id=body.resume_id,
        cover_letter=body.cover_letter,
        resume_source=body.resume_source,
        resume_optimization_id=body.resume_optimization_id,
    )
    return {
        "code": 200,
        "message": "投递成功",
        "data": result,
    }
