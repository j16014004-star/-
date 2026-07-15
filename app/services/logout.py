"""
用户登出业务逻辑层
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.logout import revoke_all_refresh_tokens


async def logout_user(db: AsyncSession, user_id: int) -> dict:
    """
    用户登出业务逻辑

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        dict: 登出结果
    """
    # 撤销用户的所有 refresh token
    revoked_count = await revoke_all_refresh_tokens(db, user_id)

    return {
        "code": 200,
        "message": "success",
        "data": None
    }
