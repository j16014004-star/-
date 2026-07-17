from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, create_two_factor_token, verify_password, verify_token
from app.crud.user_register import user_login
from app.models.user import LoginLog, RefreshToken, User
from app.schemas.user import TwoFactorLogin, UserLogin
from app.services.profile_service import verify_two_factor_code

UseLoginRouter = APIRouter(prefix="/api/auth", tags=["用户登录"])


def _request_data(request: Request) -> tuple[str | None, str | None]:
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else None)
    return ip, request.headers.get("user-agent")


async def _log(db: AsyncSession, request: Request, user_id: int | None, status: str) -> None:
    ip, ua = _request_data(request)
    db.add(LoginLog(user_id=user_id, login_ip=ip, login_location="本地网络" if ip in {"127.0.0.1", "::1"} else "未知", user_agent=ua, status=status))
    await db.flush()


async def _tokens(db: AsyncSession, request: Request, user: User) -> dict:
    claims = {"sub": str(user.id), "username": user.username, "ver": user.auth_version}
    access_token = create_access_token(claims)
    refresh_token = create_refresh_token(claims)
    ip, ua = _request_data(request)
    db.add(RefreshToken(user_id=user.id, token=refresh_token, device_info=ua, ip_address=ip, expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), is_revoked=False))
    user.last_login_at = datetime.now(timezone.utc)
    await _log(db, request, user.id, "success")
    await db.flush()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "Bearer", "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, "user": {"id": user.id, "username": user.username, "email": user.email, "avatar": user.avatar, "phone": user.phone, "status": "active"}}


@UseLoginRouter.post("/login")
async def user_login_router(user_data: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    user = await user_login(db, user_data.username)
    if user is None or not verify_password(user_data.password, user.password_hash):
        await _log(db, request, user.id if user else None, "failed")
        await db.commit()
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.is_deleted or not user.is_active:
        await _log(db, request, user.id, "failed")
        await db.commit()
        raise HTTPException(status_code=403, detail="账号已停用")
    if user.two_factor_enabled:
        token = create_two_factor_token({"sub": str(user.id), "ver": user.auth_version})
        return {"code": 200, "message": "需要两步验证", "data": {"requires_two_factor": True, "two_factor_token": token, "expires_in": 300}}
    return {"code": 200, "message": "success", "data": await _tokens(db, request, user)}


@UseLoginRouter.post("/login/two-factor")
async def login_two_factor(payload: TwoFactorLogin, request: Request, db: AsyncSession = Depends(get_db)):
    claims = verify_token(payload.two_factor_token)
    if not claims or claims.get("type") != "two_factor" or not claims.get("sub"):
        raise HTTPException(401, "两步验证会话已失效")
    user = await db.get(User, int(claims["sub"]))
    if not user or user.is_deleted or not user.is_active or user.auth_version != int(claims.get("ver", 0)):
        raise HTTPException(401, "两步验证会话已失效")
    if not await verify_two_factor_code(db, user, payload.code):
        await _log(db, request, user.id, "failed")
        await db.commit()
        raise HTTPException(401, "动态验证码或恢复码错误")
    return {"code": 200, "message": "success", "data": await _tokens(db, request, user)}
