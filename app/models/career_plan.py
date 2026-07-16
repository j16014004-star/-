"""Career planning persistence models."""
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, JSON, String, Text
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
    knowledge_base_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )
