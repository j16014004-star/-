"""
用户相关模型:
users
refresh_tokens
verification_codes
login_logs
"""

from datetime import datetime, timezone
import enum

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    BigInteger,
    Integer,
    Text,
    ForeignKey,
    Enum as SAEnum
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.core.database import Base


# 用户角色
class UserRole(str, enum.Enum):
    USER = "user"
    HR = "hr"
    ADMIN = "admin"


# =========================
# 用户表
# =========================

class User(Base):
    """用户主表"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    username: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        comment="用户名"
    )

    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="邮箱"
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        comment="手机号"
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="密码哈希"
    )

    avatar: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="头像URL"
    )

    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole),
        default=UserRole.USER,
        nullable=False,
        comment="用户角色"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活"
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="逻辑删除"
    )

    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    two_factor_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    two_factor_pending_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    auth_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


    # 关系
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


# =========================
# Refresh Token表
# =========================

class RefreshToken(Base):
    """刷新令牌表"""

    __tablename__ = "refresh_tokens"


    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )


    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )


    token: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
        comment="refresh token"
    )


    device_info: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="设备信息"
    )


    ip_address: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="IP地址"
    )


    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="过期时间"
    )


    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否撤销"
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后使用时间"
    )


    user: Mapped["User"] = relationship(
        back_populates="refresh_tokens"
    )



# =========================
# 验证码表
# =========================

class VerificationCode(Base):

    """验证码表"""

    __tablename__ = "verification_codes"


    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )


    target: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="邮箱/手机号"
    )


    code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="验证码"
    )


    purpose: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="用途"
    )


    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )


    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )



# =========================
# 登录日志表
# =========================

class LoginLog(Base):

    """登录日志"""

    __tablename__ = "login_logs"


    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )


    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )


    login_ip: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="登录IP"
    )


    login_location: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="登录地点"
    )


    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="浏览器UA"
    )


    login_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


    status: Mapped[str] = mapped_column(
        String(20),
        default="success",
        comment="登录状态"
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    push_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ai_report_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )


class TwoFactorRecoveryCode(Base):
    __tablename__ = "two_factor_recovery_codes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
