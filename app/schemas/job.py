"""岗位相关 Pydantic Schema"""
from datetime import datetime

from pydantic import BaseModel, Field


class JobResponse(BaseModel):
    """岗位列表项"""
    id: int
    company: str
    company_logo: str | None = None
    title: str
    salary_min: int | None = None
    salary_max: int | None = None
    city: str | None = None
    experience_required: str | None = None
    education_required: str | None = None
    skills: list[str] | None = None
    description: str | None = None
    match_score: int | None = None
    match_reasons: list[str] | None = None
    source: str
    source_name: str
    source_url: str | None = None
    is_active: bool = True
    crawl_time: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobDetailResponse(JobResponse):
    """岗位详情"""
    area: str | None = None
    description: str | None = None


class JobApplyRequest(BaseModel):
    """投递请求"""
    resume_id: int = Field(..., description="简历ID")
    cover_letter: str | None = Field(None, description="求职信")


class JobApplyResponse(BaseModel):
    """投递响应"""
    id: int
    job_id: int
    resume_id: int
    status: str
    apply_type: str
    applied_at: datetime

    class Config:
        from_attributes = True


class JobPaginatedResponse(BaseModel):
    """分页响应"""
    items: list[JobResponse]
    total: int
    page: int
    page_size: int
