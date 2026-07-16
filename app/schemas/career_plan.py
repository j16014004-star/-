"""Schemas for career planning."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.resume_optimization import AITaskStatus


class CareerProjectAttachmentResponse(BaseModel):
    id: int
    original_filename: str
    file_type: str
    file_size: int
    status: Literal["uploaded", "processing", "completed", "failed"]
    error_message: str | None = None


class CareerProjectInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=3000)
    role: str = Field(min_length=1, max_length=200)
    file_ids: list[int] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def normalize_text(self):
        self.name = self.name.strip()
        self.description = self.description.strip()
        self.role = self.role.strip()
        self.file_ids = list(dict.fromkeys(self.file_ids))
        return self


class CareerPlanningProfileRequest(BaseModel):
    education: str = Field(min_length=1, max_length=50)
    experience: str = Field(min_length=1, max_length=50)
    skills: list[str] = Field(min_length=1, max_length=20)
    work_description: str = Field(min_length=1, max_length=5000)
    weekly_learning_hours: int = Field(ge=1, le=80)
    preferred_target_role: str | None = Field(default=None, max_length=100)
    projects: list[CareerProjectInput] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def normalize_fields(self):
        self.education = self.education.strip()
        self.experience = self.experience.strip()
        self.skills = list(dict.fromkeys(skill.strip() for skill in self.skills if skill.strip()))
        if not self.skills:
            raise ValueError("至少填写一个技能标签")
        self.work_description = self.work_description.strip()
        if not self.work_description:
            raise ValueError("工作经历描述不能为空")
        if self.preferred_target_role is not None:
            self.preferred_target_role = self.preferred_target_role.strip() or None
        return self


class CareerPlanningProfileResponse(CareerPlanningProfileRequest):
    id: int
    created_at: datetime
    updated_at: datetime


class CareerPlanCreateRequest(BaseModel):
    profile_id: int = Field(gt=0)
    preferred_target_role: str | None = Field(default=None, max_length=100)
    plan_months: int | None = Field(default=None, ge=1, le=36)

    @model_validator(mode="after")
    def normalize_target_role(self):
        if self.preferred_target_role is not None:
            self.preferred_target_role = self.preferred_target_role.strip() or None
        return self


class CareerPlanStartResponse(BaseModel):
    task_id: str
    status: AITaskStatus
    result_id: int | None = None
    plan_id: int
    poll_after_seconds: int = 2


class RecommendedRole(BaseModel):
    role_name: str
    match_score: int = Field(ge=0, le=100)
    priority: int
    recommendation_reason: str
    matched_capabilities: list[str]
    missing_capabilities: list[str]
    suitable_industries: list[str]
    next_actions: list[str]
    is_long_term_direction: bool


class SkillGapItem(BaseModel):
    skill: str
    priority: Literal["high", "medium", "low"]
    current_level: str
    target_level: str
    reason: str


class LearningStage(BaseModel):
    stage: str
    duration: str
    goals: list[str]
    topics: list[str]
    tasks: list[str]
    practice_tasks: list[str]
    deliverables: list[str]
    acceptance_criteria: list[str]


class CareerPlanResponse(BaseModel):
    id: int
    profile_id: int
    career_profile_summary: dict
    recommended_roles: list[RecommendedRole]
    career_goals: dict
    skill_gap_analysis: list[SkillGapItem]
    learning_path: dict
    action_plan: dict
    risks_and_alternatives: dict
    retrieval_source: str | None = None
    retrieval_error: str | None = None
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    knowledge_base_version: str | None = None
    created_at: datetime


class CareerProfileSummary(BaseModel):
    current_stage: str
    core_strengths: list[str]
    transferable_skills: list[str]
    main_weaknesses: list[str]
    summary: str


class CareerGoals(BaseModel):
    short_term: list[str]
    medium_term: list[str]
    long_term: list[str]


class LearningPath(BaseModel):
    total_weeks: int = Field(ge=1)
    hours_per_week: int = Field(ge=1)
    stages: list[LearningStage]


class ActionPlan(BaseModel):
    this_week: list[str]
    this_month: list[str]
    portfolio_projects: list[str]
    resume_actions: list[str]
    review_points: list[str]


class RisksAndAlternatives(BaseModel):
    risks: list[str]
    assumptions_to_confirm: list[str]
    alternative_roles: list[str]
    adjustment_advice: list[str]


class CareerPlanAIOutput(BaseModel):
    career_profile_summary: CareerProfileSummary
    recommended_roles: list[RecommendedRole] = Field(min_length=1)
    career_goals: CareerGoals
    skill_gap_analysis: list[SkillGapItem] = Field(min_length=1)
    learning_path: LearningPath
    action_plan: ActionPlan
    risks_and_alternatives: RisksAndAlternatives
