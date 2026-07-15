'''AI task and resume optimization persistence models.'''
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


LONG_TEXT = Text().with_variant(LONGTEXT(), 'mysql')


class AITask(Base):
    '''Generic asynchronous AI task.''' 

    __tablename__ = 'ai_tasks'

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True,
    )
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(30), nullable=False)
    resource_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='pending', index=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    request_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    token_usage: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider_call_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now, onupdate=utc_now,
    )

    __table_args__ = (
        Index('ix_ai_tasks_idempotency', 'user_id', 'task_type', 'resource_id', 'input_hash'),
    )


class ResumeOptimizationVersion(Base):
    '''An immutable optimized version of a resume.'''

    __tablename__ = 'resume_optimization_versions'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True,
    )
    resume_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False, index=True,
    )
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey('ai_tasks.id', ondelete='CASCADE'), nullable=False, unique=True,
    )
    analysis_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    optimization_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    optimization_focus: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    style: Mapped[str] = mapped_column(String(30), nullable=False)
    preserve_structure: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    optimization_summary: Mapped[str] = mapped_column(Text, nullable=False)
    original_content: Mapped[str] = mapped_column(LONG_TEXT, nullable=False)
    optimized_content: Mapped[str] = mapped_column(LONG_TEXT, nullable=False)
    change_items: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    confirmation_questions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    score_improvement: Mapped[int | None] = mapped_column(Integer, nullable=True)
    knowledge_base_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    retrieved_chunk_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    resume_content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)

