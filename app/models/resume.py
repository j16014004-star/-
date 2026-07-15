"""
简历相关模型
"""
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    Text,
    BigInteger,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Resume(Base):
    """简历主表"""

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID",
    )

    title: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="简历标题",
    )

    file_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="文件类型 (pdf/doc/docx)",
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="文件存储路径",
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="文件大小（字节）",
    )

    extracted_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="提取的纯文本",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="状态: pending/processing/completed/failed",
    )

    error_message: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="错误信息",
    )

    structured_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="结构化解析结果（规则提取的基础信息、教育、工作、项目、技能）",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # 关系
    chunks: Mapped[list["ResumeChunk"]] = relationship(
        "ResumeChunk",
        back_populates="resume",
        cascade="all, delete-orphan",
    )


class ResumeChunk(Base):
    """简历分块表"""

    __tablename__ = "resume_chunks"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    resume_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="简历ID",
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="块序号（从0开始）",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="块内容",
    )

    char_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="字符数",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # 关系
    resume: Mapped["Resume"] = relationship(
        "Resume",
        back_populates="chunks",
    )
