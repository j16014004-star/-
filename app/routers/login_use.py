from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.schemas.user import UserLogin
from app.services.user_register import login_user
from app.models.user import RefreshToken


UseLoginRouter = APIRouter(prefix="/api/auth", tags=["用户登录"])



#用户登录路由
@UseLoginRouter.post("/login")
async def user_login_router(user_data: UserLogin,db: AsyncSession=Depends(get_db)):
    #调用service层验证用户名和密码
    user = await login_user(db, user_data)
    if user is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    #生成access token
    access_token = create_access_token(
        {
            "sub": str(user.id),
            "username": user.username,
        }
    )

    #生成refresh token
    refresh_token = create_refresh_token(
        {
            "sub": str(user.id),
            "username": user.username,
        }
    )

    #存储refresh token到数据库
    refresh_token_record = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        is_revoked=False
    )
    db.add(refresh_token_record)
    await db.flush()

    return {
        "code": 200,
        "message": "success",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": 7200,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "avatar": f"https://api.dicebear.com/7.x/avataaars/svg?seed={user.username}",
                "phone": user.phone,
                "status": "active" if user.is_active else "inactive",
            }
        }
    }