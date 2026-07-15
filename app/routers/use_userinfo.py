from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.user_info import format_user_info

# 用户信息路由
UseUserInfoRouter = APIRouter(prefix="/api/auth", tags=["用户信息"])


@UseUserInfoRouter.get("/userinfo")
async def get_userinfo(user: User = Depends(get_current_user)):
    """获取当前登录用户信息（通过 Bearer Token 认证）"""
    data = format_user_info(user)
    return {
        "code": 200,
        "message": "success",
        "data": data,
    }
