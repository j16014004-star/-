"""Import all ORM models so SQLAlchemy metadata can resolve foreign keys."""

from app.models.user import LoginLog, RefreshToken, User, UserRole, VerificationCode
from app.models.resume import Resume, ResumeChunk
from app.models.ai import AITask, ResumeOptimizationVersion
from app.models.career_plan import CareerPlan, CareerPlanningProfile, CareerProjectAttachment
from app.models.job import (
    Job,
    JobApplication,
    JobPlatformLoginSession,
    JobRecommendResult,
    JobRecommendTask,
)

__all__ = [
    'AITask',
    'ResumeOptimizationVersion',
    "CareerPlan",
    "CareerPlanningProfile",
    "CareerProjectAttachment",
    "LoginLog",
    "RefreshToken",
    "User",
    "UserRole",
    "VerificationCode",
    "Resume",
    "ResumeChunk",
    "Job",
    "JobApplication",
    "JobPlatformLoginSession",
    "JobRecommendResult",
    "JobRecommendTask",
]
