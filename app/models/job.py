"""
岗位相关模型
"""
from datetime import datetime, timezone

from sqlalchemy import (
    String, Text, BigInteger, Integer, Boolean, DateTime,
    ForeignKey, JSON, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Job(Base):
    """岗位信息表"""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    source_id: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="爬虫来源平台岗位ID（用于去重）"
    )
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="来源平台: 58/boss/lagou/liepin"
    )
    source_name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="来源平台名称: 58同城/BOSS直聘"
    )
    source_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="原始岗位链接"
    )

    company: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="公司名称"
    )
    company_logo: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="公司Logo URL"
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="岗位名称"
    )

    salary_min: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="最低薪资（元/月）"
    )
    salary_max: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="最高薪资（元/月）"
    )

    city: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="工作城市"
    )
    area: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="区域/区县"
    )
    experience_required: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="经验要求"
    )
    education_required: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="学历要求"
    )

    skills: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, comment="技能标签列表"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="完整岗位描述"
    )

    match_score: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="AI匹配分数（暂未实现）"
    )
    match_reasons: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="AI匹配原因（暂未实现）"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否有效"
    )

    crawl_time: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="最近爬取时间"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_job_source"),
    )


class JobApplication(Base):
    """用户投递记录表"""

    __tablename__ = "job_applications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="用户ID",
    )
    job_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="岗位ID",
    )
    resume_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="投递使用的简历ID",
    )

    cover_letter: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="求职信",
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False,
        comment="状态: pending/viewed/interview/rejected/accepted",
    )
    apply_type: Mapped[str] = mapped_column(
        String(20), default="manual", nullable=False, comment="投递类型: manual",
    )

    applied_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )


class JobPlatformLoginSession(Base):
    """招聘平台用户登录会话"""

    __tablename__ = "job_platform_login_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="用户ID",
    )
    resume_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False, comment="关联简历ID",
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False, comment="招聘平台")
    status: Mapped[str] = mapped_column(
        String(20), default="waiting_login", nullable=False,
        comment="waiting_login/logged_in/expired/failed",
    )
    storage_state_ref: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="服务端私有登录态文件引用",
    )
    error_message: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="脱敏错误信息",
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False,
    )


class JobRecommendTask(Base):
    """简历驱动的岗位推荐任务"""

    __tablename__ = "job_recommend_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="用户ID",
    )
    resume_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="简历ID",
    )
    login_session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("job_platform_login_sessions.id", ondelete="SET NULL"),
        nullable=True, comment="登录会话ID",
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False, comment="招聘平台")
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False,
        comment="pending/crawling/matching/success/failed/need_login",
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extracted_skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    search_keywords: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    requested_limit: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    total_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_saved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_matched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False,
    )


class JobRecommendResult(Base):
    """任务专属的岗位推荐结果"""

    __tablename__ = "job_recommend_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_recommend_tasks.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    resume_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    match_score: Mapped[int] = mapped_column(Integer, nullable=False)
    matched_skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    matched_skill_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    match_reasons: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("task_id", "job_id", name="uq_recommend_task_job"),
    )

