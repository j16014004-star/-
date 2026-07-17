from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.profile import AccountDelete, PasswordChange, PreferenceUpdate, ProfileUpdate, TwoFactorDisable, TwoFactorEnable, TwoFactorSetup
from app.services import profile_service

router = APIRouter(prefix="/api/auth", tags=["个人中心"])

def ok(data=None, message="success"):
    return {"code": 200, "message": message, "data": data}

@router.put("/profile")
async def profile(payload: ProfileUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return ok(await profile_service.update_profile(db, user, payload.username))

@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return ok({"avatar_url": await profile_service.save_avatar(db, user, file)})

@router.delete("/avatar")
async def delete_avatar(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await profile_service.remove_avatar(db, user)
    return ok()

@router.put("/password")
async def password(payload: PasswordChange, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await profile_service.change_password(db, user, payload.current_password, payload.new_password)
    return ok({"requires_relogin": True}, "密码已修改，请重新登录")

@router.post("/two-factor/setup")
async def two_factor_setup(payload: TwoFactorSetup, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return ok(await profile_service.setup_two_factor(db, user, payload.password))

@router.post("/two-factor/enable")
async def two_factor_enable(payload: TwoFactorEnable, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return ok(await profile_service.enable_two_factor(db, user, payload.code))

@router.post("/two-factor/disable")
async def two_factor_disable(payload: TwoFactorDisable, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return ok(await profile_service.disable_two_factor(db, user, payload.password, payload.code))

@router.get("/login-logs")
async def login_logs(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return ok(await profile_service.get_login_logs(db, user.id, page, page_size))

@router.get("/preferences")
async def preferences(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return ok(profile_service.preference_data(await profile_service.get_preferences(db, user.id)))

@router.put("/preferences")
async def update_preferences(payload: PreferenceUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    value = await profile_service.get_preferences(db, user.id)
    for name in payload.model_fields_set:
        setattr(value, name, getattr(payload, name))
    await db.flush()
    return ok(profile_service.preference_data(value))

@router.delete("/account")
async def account(payload: AccountDelete, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await profile_service.delete_account(db, user, payload.password, payload.confirmation, payload.code)
    return ok()
