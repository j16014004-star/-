"""
Token 刷新业务逻辑层
"""
from datetime import datetime, timezone
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_token, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.crud.refresh_token import get_refresh_token_by_token, update_last_used_at
from app.models.user import User


async def refresh_access_token(db: AsyncSession, refresh_token_str: str) -> tuple[str, int] | None:
    """
    刷新访问令牌

    业务流程：
    1. 验证 refresh_token 的 JWT 签名和有效期
    2. 检查 token 是否在数据库中存在且未被撤销
    3. 检查 token 是否已过期
    4. 生成新的 access_token
    5. 更新 refresh_token 的 last_used_at

    Args:
        db: 数据库会话
        refresh_token_str: refresh token 字符串

    Returns:
        tuple: (新的 access_token, 过期时间秒数)
        None: 如果验证失败
    """
    # 1. 验证 JWT 签名和有效期
    payload = verify_token(refresh_token_str)
    if payload is None:
        return None

    # 2. 检查 token 类型
    token_type = payload.get("type")
    if token_type != "refresh":
        return None

    # 3. 从数据库查询 token 记录
    refresh_token_record = await get_refresh_token_by_token(db, refresh_token_str)
    if refresh_token_record is None:
        return None

    # 4. 检查是否被撤销
    if refresh_token_record.is_revoked:
        return None

    # 5. 检查是否过期
    # 数据库中的 datetime 可能是 offset-naive，需要统一处理
    expires_at = refresh_token_record.expires_at
    if expires_at.tzinfo is None:
        # 如果是 offset-naive，假设是 UTC 时间
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        return None

    # 6. 生成新的 access_token
    user_id = payload.get("sub")
    username = payload.get("username")

    if not user_id or not username:
        return None
    user = await db.get(User, int(user_id))
    if not user or user.is_deleted or not user.is_active or user.auth_version != int(payload.get("ver", 0)):
        return None

    new_access_token = create_access_token(data={
        "sub": str(user_id),
        "username": username,
        "ver": user.auth_version,
    })

    # 7. 更新 last_used_at
    await update_last_used_at(db, refresh_token_record)

    # 8. 返回新 token 和过期时间
    expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 转换为秒
    return new_access_token, expires_in
