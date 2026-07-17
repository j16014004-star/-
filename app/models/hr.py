"""HR assistant workspace, confirmation action and audit log models."""
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


LONG_TEXT = Text().with_variant(LONGTEXT(), "mysql")


class HrWorkspace(Base):
    __tablename__ = "hr_workspaces"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="58")
    resume_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_source: Mapped[str] = mapped_column(String(20), nullable=False, default="original")
    resume_optimization_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("resume_optimization_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    login_session_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("job_platform_login_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    ai_task_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ai_tasks.id", ondelete="SET NULL"), nullable=True
    )
    automation_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="assisted")
    permissions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    manual_login_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft", index=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[str | None] = mapped_column(String(200), nullable=True)
    hr_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unread_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pending_confirmation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    platform_thread_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    platform_conversation_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    platform_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sync_status: Mapped[str] = mapped_column(String(30), nullable=False, default="never")
    sync_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        Index("ix_hr_workspaces_user_status", "user_id", "status"),
        Index("ix_hr_workspaces_selection", "user_id", "job_id", "resume_id"),
    )


class HrPendingAction(Base):
    __tablename__ = "hr_pending_actions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("hr_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="waiting_confirmation", index=True
    )
    content: Mapped[str] = mapped_column(LONG_TEXT, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    requires_confirmation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    confirmation_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )


class HrActionLog(Base):
    __tablename__ = "hr_action_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("hr_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)


class HrMessage(Base):
    __tablename__ = "hr_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("hr_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("hr_pending_actions.id", ondelete="SET NULL"), nullable=True
    )
    sender_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(LONG_TEXT, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending_confirmation")
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_confirmation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    platform_message_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    __table_args__ = (Index("ix_hr_messages_workspace_created", "workspace_id", "created_at"),)


class HrInterview(Base):
    __tablename__ = "hr_interviews"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("hr_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_message_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("hr_messages.id", ondelete="SET NULL"), nullable=True
    )
    action_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("hr_pending_actions.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="proposed", index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="Asia/Shanghai")
    interview_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meeting_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    evidence: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    missing_fields: Mapped[list | None] = mapped_column(JSON, nullable=True)
    suggested_reply: Mapped[str | None] = mapped_column(LONG_TEXT, nullable=True)
    requires_confirmation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now
    )

    __table_args__ = (Index("ix_hr_interviews_user_schedule", "user_id", "scheduled_at"),)
