"""岗位平台与任务 API Schema"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class RecommendIntentMixin(BaseModel):
    target_role: str | None = Field(default=None, max_length=100)
    target_city: str | None = Field(default=None, max_length=50)
    resume_source: Literal["original", "optimized"] = "original"
    resume_optimization_id: int | None = Field(default=None, gt=0)

    @field_validator("target_role", "target_city")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return " ".join(value.split()).strip() or None if value else None

    @model_validator(mode="after")
    def validate_resume_selection(self):
        if self.resume_source == "optimized" and self.resume_optimization_id is None:
            raise ValueError("选择优化简历时必须提交 resume_optimization_id")
        if self.resume_source == "original" and self.resume_optimization_id is not None:
            raise ValueError("选择原始简历时不能提交 resume_optimization_id")
        return self


class PlatformLoginStartRequest(RecommendIntentMixin):
    target_role: str = Field(min_length=1, max_length=100)
    target_city: str = Field(min_length=1, max_length=50)
    source: Literal["58"]
    resume_id: int = Field(gt=0)
    limit: int = Field(default=20, ge=1, le=50)
    force_refresh: bool = False

    @model_validator(mode="after")
    def require_search_intent(self):
        if not self.target_role or not self.target_city:
            raise ValueError("target_role 和 target_city 均为必填项")
        return self


class RecommendTaskStartRequest(RecommendIntentMixin):
    resume_id: int = Field(gt=0)
    source: Literal["58"]
    login_session_id: str = Field(min_length=36, max_length=36)
    limit: int = Field(default=20, ge=1, le=50)
    force_refresh: bool = False


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
    login_mode: Literal["server_browser", "remote_browser"] = "server_browser"
    login_url: str
    browser_url: str | None = None
    expires_at: datetime
    error_message: str | None = None
    recommend_task_id: str | None = None
    recommend_status: str | None = None
    recommend_poll_after_seconds: int | None = None
    poll_after_seconds: int = 2


class RecommendTaskResponse(BaseModel):
    task_id: str
    login_session_id: str | None = None
    status: str
    resume_id: int
    resume_source: Literal["original", "optimized"]
    resume_optimization_id: int | None
    source: str
    source_name: str
    target_role: str
    target_city: str
    extracted_skills: list[str]
    search_keywords: list[str]
    poll_after_seconds: int = 2


class RecommendTaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    source: str
    resume_id: int
    resume_source: Literal["original", "optimized"]
    resume_optimization_id: int | None
    target_role: str
    target_city: str
    extracted_skills: list[str]
    search_keywords: list[str]
    total_found: int
    total_saved: int
    total_matched: int
    failure_code: str | None
    error_message: str | None
    crawl_diagnostics: dict | None
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
