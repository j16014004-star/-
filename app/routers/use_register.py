from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.user import UserLogin, UserRegister
from app.services.user_register import login_user, register_user

# 用户注册路由
UseRegisterRouter = APIRouter(prefix="/api/auth", tags=["用户注册"])

@UseRegisterRouter.post("/register")
async def user_register(user_data: UserRegister,db: AsyncSession=Depends(get_db)):
    users = await register_user(db, user_data)
    if users is None:
        raise HTTPException(status_code=400, detail="用户已存在")
    return {
        "code": 200,
        "message": "注册成功",
        "data": {
            "id": users.id,
            "username": users.username,
            "email": users.email
        }
    }

