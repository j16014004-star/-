"""
用户登出数据访问层
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from app.models.user import RefreshToken


async def revoke_all_refresh_tokens(db: AsyncSession, user_id: int) -> int:
    """
    撤销用户的所有 refresh token

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        int: 被撤销的 token 数量
    """
    result = await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id)
        .where(RefreshToken.is_revoked == False)
        .values(is_revoked=True)
    )
    await db.flush()
    return result.rowcount
