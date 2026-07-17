"""岗位相关 Pydantic Schema"""
from datetime import datetime

from typing import Literal
from pydantic import BaseModel, Field, model_validator


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
    resume_source: Literal["original", "optimized"] = "original"
    resume_optimization_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_resume_selection(self):
        if self.resume_source == "optimized" and self.resume_optimization_id is None:
            raise ValueError("选择优化简历时必须提交 resume_optimization_id")
        if self.resume_source == "original" and self.resume_optimization_id is not None:
            raise ValueError("选择原始简历时不能提交 resume_optimization_id")
        return self


class JobApplyResponse(BaseModel):
    """投递响应"""
    id: int
    job_id: int
    resume_id: int
    resume_source: str
    resume_optimization_id: int | None
    status: str
    apply_type: str
    delivery_evidence: dict | None = None
    applied_at: datetime

    class Config:
        from_attributes = True


class JobPaginatedResponse(BaseModel):
    """分页响应"""
    items: list[JobResponse]
    total: int
    page: int
    page_size: int
