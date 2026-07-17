"""Import all ORM models so SQLAlchemy metadata can resolve foreign keys."""

from app.models.user import (
    LoginLog, RefreshToken, TwoFactorRecoveryCode, User, UserPreference,
    UserRole, VerificationCode,
)
from app.models.resume import Resume, ResumeChunk
from app.models.ai import AITask, ResumeOptimizationVersion
from app.models.career_plan import (
    CareerPlan,
    CareerPlanCheckin,
    CareerPlanExecution,
    CareerPlanExecutionTask,
    CareerPlanQuestion,
    CareerStageAssessment,
    CareerStageAssessmentAnswer,
    CareerStageAssessmentQuestion,
    CareerStageProgress,
    CareerPlanningProfile,
    CareerProjectAttachment,
)
from app.models.job import (
    Job,
    JobApplication,
    JobPlatformLoginSession,
    JobRecommendResult,
    JobRecommendTask,
)
from app.models.hr import HrActionLog, HrInterview, HrMessage, HrPendingAction, HrWorkspace
from app.models.mock_interview import (
    MockInterview,
    MockInterviewAnswer,
    MockInterviewQuestion,
    MockInterviewQuestionRecommendation,
    MockInterviewReport,
)

__all__ = [
    'AITask',
    'ResumeOptimizationVersion',
    "CareerPlan",
    "CareerPlanCheckin",
    "CareerPlanExecution",
    "CareerPlanExecutionTask",
    "CareerPlanQuestion",
    "CareerStageAssessment",
    "CareerStageAssessmentAnswer",
    "CareerStageAssessmentQuestion",
    "CareerStageProgress",
    "CareerPlanningProfile",
    "CareerProjectAttachment",
    "LoginLog",
    "RefreshToken",
    "User",
    "UserRole",
    "VerificationCode",
    "UserPreference",
    "TwoFactorRecoveryCode",
    "Resume",
    "ResumeChunk",
    "Job",
    "JobApplication",
    "JobPlatformLoginSession",
    "JobRecommendResult",
    "JobRecommendTask",
    "HrWorkspace",
    "HrPendingAction",
    "HrActionLog",
    "HrMessage",
    "HrInterview",
    "MockInterview",
    "MockInterviewQuestion",
    "MockInterviewAnswer",
    "MockInterviewReport",
    "MockInterviewQuestionRecommendation",
]
