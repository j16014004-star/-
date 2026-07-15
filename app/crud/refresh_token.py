"""
Refresh Token 数据访问层
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import RefreshToken


async def get_refresh_token_by_token(db: AsyncSession, token: str) -> RefreshToken | None:
    """
    根据 token 字符串查询 RefreshToken 记录

    Args:
        db: 数据库会话
        token: refresh token 字符串

    Returns:
        RefreshToken 对象，如果不存在返回 None
    """
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == token)
    )
    return result.scalar_one_or_none()


async def update_last_used_at(db: AsyncSession, refresh_token: RefreshToken) -> None:
    """
    更新 refresh token 的最后使用时间

    Args:
        db: 数据库会话
        refresh_token: RefreshToken 对象
    """
    from datetime import datetime, timezone
    refresh_token.last_used_at = datetime.now(timezone.utc)
    db.add(refresh_token)
    await db.flush()
