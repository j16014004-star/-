"""
用户登出路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.logout import logout_user

router = APIRouter(prefix="/api/auth", tags=["用户登出"])


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    用户登出

    - 撤销用户的所有 refresh token
    - 需要 Bearer Token 认证
    """
    result = await logout_user(db, current_user.id)
    return result
