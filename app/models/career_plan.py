"""Career planning persistence models."""
from datetime import date, datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


LONG_TEXT = Text().with_variant(LONGTEXT(), "mysql")


class CareerProjectAttachment(Base):
    """Uploaded project attachment used as evidence for career planning."""

    __tablename__ = "career_project_attachments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(LONG_TEXT, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )


class CareerPlanningProfile(Base):
    """User career planning input profile."""

    __tablename__ = "career_planning_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    education: Mapped[str] = mapped_column(String(50), nullable=False)
    experience: Mapped[str] = mapped_column(String(50), nullable=False)
    skills: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    work_description: Mapped[str] = mapped_column(LONG_TEXT, nullable=False)
    weekly_learning_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    preferred_target_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    projects: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )


class CareerPlan(Base):
    """Generated career plan result."""

    __tablename__ = "career_plans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    profile_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("career_planning_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ai_tasks.id", ondelete="SET NULL"), nullable=True, unique=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="processing")
    career_profile_summary: Mapped[dict] = mapped_column(JSON, nullable=False)
    recommended_roles: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    career_goals: Mapped[dict] = mapped_column(JSON, nullable=False)
    skill_gap_analysis: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    learning_path: Mapped[dict] = mapped_column(JSON, nullable=False)
    action_plan: Mapped[dict] = mapped_column(JSON, nullable=False)
    risks_and_alternatives: Mapped[dict] = mapped_column(JSON, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    retrieval_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    retrieval_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    retrieved_chunk_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    retrieval_audit: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    knowledge_base_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    previous_plan_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("career_plans.id", ondelete="SET NULL"), nullable=True, index=True
    )
    regeneration_feedback: Mapped[str | None] = mapped_column(LONG_TEXT, nullable=True)
    regeneration_focus_areas: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )


class CareerPlanExecution(Base):
    """The active execution schedule created from an accepted career plan."""

    __tablename__ = "career_plan_executions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    career_plan_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("career_plans.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        Index("ix_career_plan_executions_user_status", "user_id", "status"),
    )


class CareerPlanExecutionTask(Base):
    """A daily or weekly task generated from an accepted plan."""

    __tablename__ = "career_plan_execution_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    execution_plan_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("career_plan_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_key: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(20), nullable=False)
    stage: Mapped[str] = mapped_column(String(200), nullable=False)
    week_no: Mapped[int] = mapped_column(Integer, nullable=False)
    planned_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    checkin_note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    task_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_advanced: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    original_planned_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    advanced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_remediation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    remediation_assessment_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        UniqueConstraint("execution_plan_id", "task_key", name="uq_career_execution_task_key"),
        Index("ix_career_execution_tasks_week", "execution_plan_id", "week_no"),
    )


class CareerPlanCheckin(Base):
    """Immutable status-change history for execution task check-ins."""

    __tablename__ = "career_plan_checkins"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("career_plan_execution_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)
    checked_in_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)


class CareerPlanQuestion(Base):
    """An asynchronous AI answer attached to one execution task."""

    __tablename__ = "career_plan_questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    execution_task_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("career_plan_execution_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ai_task_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ai_tasks.id", ondelete="SET NULL"), nullable=True, unique=True
    )
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(LONG_TEXT, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sensitive_redacted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    retrieval_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    retrieval_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    retrieved_chunk_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    retrieval_audit: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    knowledge_base_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "execution_task_id", "input_hash", name="uq_career_question_input"
        ),
        Index("ix_career_questions_user_created", "user_id", "created_at"),
    )


class CareerStageProgress(Base):
    """Persistent state of one ordered stage in an accepted career plan."""

    __tablename__ = "career_stage_progress"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    execution_plan_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("career_plan_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(200), nullable=False)
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="locked", index=True)
    passed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (UniqueConstraint("execution_plan_id", "stage_order", name="uq_career_stage_order"),)


class CareerStageAssessment(Base):
    """Generated assessment and its durable evaluation result."""

    __tablename__ = "career_stage_assessments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    execution_plan_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("career_plan_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_progress_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("career_stage_progress.id", ondelete="CASCADE"), nullable=False, index=True)
    generation_task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ai_tasks.id", ondelete="SET NULL"), nullable=True, unique=True)
    evaluation_task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ai_tasks.id", ondelete="SET NULL"), nullable=True, unique=True)
    stage: Mapped[str] = mapped_column(String(200), nullable=False)
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="generating", index=True)
    passing_score: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str | None] = mapped_column(LONG_TEXT, nullable=True)
    strengths: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    weaknesses: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    improvement_advice: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    question_results: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    retrieval_audit: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)


class CareerStageAssessmentQuestion(Base):
    __tablename__ = "career_stage_assessment_questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assessment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("career_stage_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_order: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[object | None] = mapped_column(JSON, nullable=True)
    reference_answer: Mapped[str | None] = mapped_column(LONG_TEXT, nullable=True)
    rubric: Mapped[str | None] = mapped_column(LONG_TEXT, nullable=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    code_language: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)

    __table_args__ = (UniqueConstraint("assessment_id", "question_order", name="uq_career_assessment_question_order"),)


class CareerStageAssessmentAnswer(Base):
    __tablename__ = "career_stage_assessment_answers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    assessment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("career_stage_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("career_stage_assessment_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    answer: Mapped[object] = mapped_column(JSON, nullable=False)
    rule_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scoring_rationale: Mapped[str | None] = mapped_column(LONG_TEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)

    __table_args__ = (UniqueConstraint("assessment_id", "question_id", name="uq_career_assessment_answer"),)
