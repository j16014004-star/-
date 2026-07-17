import base64
import hashlib
import hmac
import io
import secrets
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pyotp
import qrcode
from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from user_agents import parse as parse_user_agent

from app.core.config import settings
from app.core.security import decrypt_totp_secret, encrypt_totp_secret, hash_password, verify_password
from app.models.user import LoginLog, RefreshToken, TwoFactorRecoveryCode, User, UserPreference
from app.services.user_info import format_user_info

AVATAR_ROOT = (Path(settings.UPLOAD_DIR) / "avatars").resolve()


def _recovery_hash(code: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), code.upper().encode(), hashlib.sha256).hexdigest()


async def update_profile(db: AsyncSession, user: User, username: str) -> dict:
    username = username.strip()
    exists = await db.scalar(select(User.id).where(User.username == username, User.id != user.id))
    if exists:
        raise HTTPException(409, "用户名已被使用")
    user.username = username
    try:
        await db.flush()
    except IntegrityError as exc:
        raise HTTPException(409, "用户名已被使用") from exc
    return format_user_info(user)


async def save_avatar(db: AsyncSession, user: User, upload: UploadFile) -> str:
    content = await upload.read(2 * 1024 * 1024 + 1)
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(413, "头像不能超过 2MB")
    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
        with Image.open(io.BytesIO(content)) as image:
            fmt = image.format
            width, height = image.size
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(400, "头像文件无效") from exc
    if fmt not in {"JPEG", "PNG"} or width > 4096 or height > 4096:
        raise HTTPException(400, "只允许 4096×4096 以内的 JPG、PNG 图片")
    suffix = ".jpg" if fmt == "JPEG" else ".png"
    user_dir = (AVATAR_ROOT / str(user.id)).resolve()
    if user_dir.parent != AVATAR_ROOT:
        raise HTTPException(400, "头像路径无效")
    user_dir.mkdir(parents=True, exist_ok=True)
    new_path = user_dir / f"avatar_{uuid.uuid4().hex}{suffix}"
    new_path.write_bytes(content)
    old_url = user.avatar
    user.avatar = f"/api/uploads/avatars/{user.id}/{new_path.name}"
    try:
        await db.flush()
    except Exception:
        new_path.unlink(missing_ok=True)
        raise
    _delete_avatar_file(old_url, user.id)
    return user.avatar


def _delete_avatar_file(url: str | None, user_id: int) -> None:
    accepted_prefixes = (
        f"/uploads/avatars/{user_id}/",
        f"/api/uploads/avatars/{user_id}/",
    )
    if not url or not url.startswith(accepted_prefixes):
        return
    path = (AVATAR_ROOT / str(user_id) / Path(url).name).resolve()
    if path.parent == (AVATAR_ROOT / str(user_id)).resolve():
        path.unlink(missing_ok=True)


async def remove_avatar(db: AsyncSession, user: User) -> None:
    old = user.avatar
    user.avatar = None
    await db.flush()
    _delete_avatar_file(old, user.id)


async def change_password(db: AsyncSession, user: User, current: str, new: str) -> None:
    if not verify_password(current, user.password_hash):
        raise HTTPException(400, "当前密码错误")
    if verify_password(new, user.password_hash):
        raise HTTPException(400, "新密码不能与当前密码相同")
    user.password_hash = hash_password(new)
    user.auth_version += 1
    await db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id).values(is_revoked=True))
    await db.flush()


async def setup_two_factor(db: AsyncSession, user: User, password: str) -> dict:
    if not verify_password(password, user.password_hash):
        raise HTTPException(400, "当前密码错误")
    secret = pyotp.random_base32()
    user.two_factor_pending_secret_encrypted = encrypt_totp_secret(secret)
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=settings.APP_NAME)
    image = qrcode.make(uri)
    output = io.BytesIO()
    image.save(output, format="PNG")
    await db.flush()
    return {"secret": secret, "qr_code_data_url": "data:image/png;base64," + base64.b64encode(output.getvalue()).decode(), "recovery_codes": []}


async def enable_two_factor(db: AsyncSession, user: User, code: str) -> dict:
    if not user.two_factor_pending_secret_encrypted:
        raise HTTPException(400, "请先初始化两步验证")
    secret = decrypt_totp_secret(user.two_factor_pending_secret_encrypted)
    if not pyotp.TOTP(secret).verify(code.replace(" ", ""), valid_window=1):
        raise HTTPException(400, "动态验证码错误")
    recovery_codes = [f"{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}" for _ in range(8)]
    await db.execute(delete(TwoFactorRecoveryCode).where(TwoFactorRecoveryCode.user_id == user.id))
    db.add_all([TwoFactorRecoveryCode(user_id=user.id, code_hash=_recovery_hash(item)) for item in recovery_codes])
    user.two_factor_secret_encrypted = user.two_factor_pending_secret_encrypted
    user.two_factor_pending_secret_encrypted = None
    user.two_factor_enabled = True
    await db.flush()
    return {"enabled": True, "recovery_codes": recovery_codes}


async def verify_two_factor_code(db: AsyncSession, user: User, code: str) -> bool:
    normalized = code.replace(" ", "").upper()
    if user.two_factor_secret_encrypted:
        secret = decrypt_totp_secret(user.two_factor_secret_encrypted)
        if pyotp.TOTP(secret).verify(normalized, valid_window=1):
            return True
    recovery = await db.scalar(select(TwoFactorRecoveryCode).where(
        TwoFactorRecoveryCode.user_id == user.id,
        TwoFactorRecoveryCode.code_hash == _recovery_hash(normalized),
        TwoFactorRecoveryCode.is_used.is_(False),
    ))
    if recovery:
        recovery.is_used = True
        recovery.used_at = datetime.now(timezone.utc)
        return True
    return False


async def disable_two_factor(db: AsyncSession, user: User, password: str, code: str) -> dict:
    if not user.two_factor_enabled:
        return {"enabled": False}
    if not verify_password(password, user.password_hash):
        raise HTTPException(400, "当前密码错误")
    if not await verify_two_factor_code(db, user, code):
        raise HTTPException(400, "动态验证码或恢复码错误")
    user.two_factor_enabled = False
    user.two_factor_secret_encrypted = None
    user.two_factor_pending_secret_encrypted = None
    await db.execute(delete(TwoFactorRecoveryCode).where(TwoFactorRecoveryCode.user_id == user.id))
    await db.flush()
    return {"enabled": False}


async def get_preferences(db: AsyncSession, user_id: int) -> UserPreference:
    preference = await db.get(UserPreference, user_id)
    if preference is None:
        preference = UserPreference(user_id=user_id)
        db.add(preference)
        await db.flush()
    return preference


def preference_data(value: UserPreference) -> dict:
    return {"email_notifications": value.email_notifications, "push_notifications": value.push_notifications, "ai_report_notifications": value.ai_report_notifications}


async def get_login_logs(db: AsyncSession, user_id: int, page: int, page_size: int) -> dict:
    base = select(LoginLog).where(LoginLog.user_id == user_id)
    total = await db.scalar(select(func.count()).select_from(LoginLog).where(LoginLog.user_id == user_id)) or 0
    records = (await db.scalars(base.order_by(LoginLog.login_time.desc()).offset((page - 1) * page_size).limit(page_size))).all()
    items = []
    for record in records:
        ua = parse_user_agent(record.user_agent or "")
        items.append({"id": record.id, "login_time": record.login_time, "ip_address": record.login_ip, "location": record.login_location or "未知", "device": ua.device.family or ("Desktop" if ua.is_pc else "Unknown"), "browser": ua.browser.family or "Unknown", "operating_system": ua.os.family or "Unknown", "status": record.status})
    return {"items": items, "total": total, "page": page, "page_size": page_size}


async def delete_account(db: AsyncSession, user: User, password: str, confirmation: str, code: str | None) -> None:
    if confirmation != "确认删除" or not verify_password(password, user.password_hash):
        raise HTTPException(400, "密码或确认文字错误")
    if user.two_factor_enabled and (not code or not await verify_two_factor_code(db, user, code)):
        raise HTTPException(400, "需要正确的动态验证码或恢复码")
    quarantine_root = (Path(settings.UPLOAD_DIR) / ".account-deletion").resolve()
    moved: list[tuple[Path, Path]] = []
    roots = [Path(settings.UPLOAD_DIR) / "resumes", Path(settings.UPLOAD_DIR) / "career_projects", Path(settings.UPLOAD_DIR) / "avatars", Path(settings.PLATFORM_STATE_DIR)]
    try:
        for root in roots:
            root = root.resolve()
            source = (root / str(user.id)).resolve()
            if source.parent == root and source.exists():
                quarantine_root.mkdir(parents=True, exist_ok=True)
                target = quarantine_root / f"{user.id}_{uuid.uuid4().hex}_{root.name}"
                source.replace(target)
                moved.append((source, target))
        marker = uuid.uuid4().hex
        user.username = f"deleted_{user.id}_{marker[:8]}"
        user.email = f"deleted_{user.id}_{marker}@invalid.local"
        user.phone = None
        user.avatar = None
        user.password_hash = hash_password(secrets.token_urlsafe(32))
        user.is_active = False
        user.is_deleted = True
        user.auth_version += 1
        user.two_factor_enabled = False
        user.two_factor_secret_encrypted = None
        user.two_factor_pending_secret_encrypted = None
        await db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id).values(is_revoked=True))
        await db.execute(delete(TwoFactorRecoveryCode).where(TwoFactorRecoveryCode.user_id == user.id))
        await db.commit()
    except Exception:
        await db.rollback()
        for source, target in reversed(moved):
            if target.exists() and not source.exists():
                source.parent.mkdir(parents=True, exist_ok=True)
                target.replace(source)
        raise
    for _, target in moved:
        shutil.rmtree(target, ignore_errors=True)
