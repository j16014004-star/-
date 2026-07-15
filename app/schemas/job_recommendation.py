"""岗位平台与任务 API Schema"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PlatformLoginStartRequest(BaseModel):
    source: Literal["58"]
    resume_id: int = Field(gt=0)
    limit: int = Field(default=20, ge=1, le=50)


class RecommendTaskStartRequest(BaseModel):
    resume_id: int = Field(gt=0)
    source: Literal["58"]
    login_session_id: str = Field(min_length=36, max_length=36)
    limit: int = Field(default=20, ge=1, le=50)


class PlatformInfo(BaseModel):
    source: str
    name: str
    enabled: bool
    login_required: bool
    login_status: str


class LoginSessionResponse(BaseModel):
    login_session_id: str
    source: str
    source_name: str
    status: str
    login_url: str
    expires_at: datetime
    error_message: str | None = None
    recommend_task_id: str | None = None
    recommend_status: str | None = None
    recommend_poll_after_seconds: int | None = None
    poll_after_seconds: int = 2


class RecommendTaskResponse(BaseModel):
    task_id: str
    status: str
    resume_id: int
    source: str
    source_name: str
    extracted_skills: list[str]
    poll_after_seconds: int = 2


class RecommendTaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    source: str
    resume_id: int
    extracted_skills: list[str]
    total_found: int
    total_saved: int
    total_matched: int
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class RecommendResultResponse(BaseModel):
    id: int
    company: str
    company_logo: str | None
    title: str
    salary_min: int | None
    salary_max: int | None
    city: str | None
    experience_required: str | None
    education_required: str | None
    skills: list[str]
    match_score: int
    matched_skills: list[str]
    match_reasons: list[str]
    source: str
    source_name: str
    source_url: str | None
    crawl_time: datetime | None
