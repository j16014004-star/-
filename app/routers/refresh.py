"""
Token 刷新路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.token import TokenRefreshRequest, TokenRefreshResponse
from app.services.refresh import refresh_access_token

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/refresh", response_model=dict)
async def refresh_token(
    request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    刷新访问令牌

    - 验证 refresh_token 的有效性
    - 生成新的 access_token
    - 更新 refresh_token 的最后使用时间
    """
    result = await refresh_access_token(db, request.refresh_token)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_access_token, expires_in = result

    return {
        "code": 200,
        "message": "success",
        "data": {
            "access_token": new_access_token,
            "expires_in": expires_in
        }
    }
