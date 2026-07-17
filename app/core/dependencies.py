from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User
#bearer token 认证
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    #1.获取token
    token = credentials.credentials
    #2.解析token
    payload = verify_token(token)
    
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="无效的token")
    
    #3.获取用户id
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="数据错误")
    
    #4不为空则查询用户实现免登录功能
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None or user.is_deleted or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已停用")
    if int(payload.get("ver", 0)) != user.auth_version:
        raise HTTPException(status_code=401, detail="登录状态已失效，请重新登录")
    
    return user
