"""招聘平台 storage-state 加密、读取与基础校验。"""
import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

LOGIN_URLS = {"58": "https://passport.58.com/login"}


def _fernet() -> Fernet:
    configured = settings.PLATFORM_STATE_ENCRYPTION_KEY.strip().encode("utf-8")
    if configured:
        return Fernet(configured)
    derived = hashlib.sha256(
        f"{settings.SECRET_KEY}:platform-storage-state:v1".encode("utf-8")
    ).digest()
    return Fernet(base64.urlsafe_b64encode(derived))


def load_storage_state(state_path: str | Path) -> dict:
    """Decrypt an encrypted state file; legacy JSON is read for migration only."""
    path = Path(state_path)
    raw = path.read_bytes()
    if path.suffix.lower() == ".enc":
        try:
            raw = _fernet().decrypt(raw)
        except InvalidToken as exc:
            raise ValueError("招聘平台登录态解密失败") from exc
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("cookies"), list):
        raise ValueError("招聘平台登录态格式无效")
    return payload


def encrypt_storage_state_file(plain_path: str | Path, encrypted_path: str | Path) -> Path:
    """Atomically encrypt a Playwright JSON storage state and remove plaintext."""
    source = Path(plain_path)
    destination = Path(encrypted_path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("cookies"), list):
        raise ValueError("招聘平台登录态格式无效")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(destination.suffix + ".tmp")
    temp_path.write_bytes(_fernet().encrypt(json.dumps(payload).encode("utf-8")))
    os.chmod(temp_path, 0o600)
    temp_path.replace(destination)
    source.unlink(missing_ok=True)
    return destination


def secure_state_path(user_id: int, source: str) -> Path:
    state_dir = Path(settings.PLATFORM_STATE_DIR).resolve() / str(user_id)
    encrypted = state_dir / f"{source}.enc"
    legacy = state_dir / f"{source}.json"
    if encrypted.is_file():
        return encrypted
    if legacy.is_file():
        try:
            return encrypt_storage_state_file(legacy, encrypted)
        except (OSError, ValueError, TypeError):
            return legacy
    return encrypted


def remove_storage_state(state_path: str | Path) -> None:
    path = Path(state_path)
    for candidate in (path, path.with_suffix(path.suffix + ".tmp")):
        try:
            candidate.unlink(missing_ok=True)
        except OSError:
            pass


def is_plausible_storage_state(state_path: str | Path, source: str) -> bool:
    """检查文件格式、平台域名、认证 Cookie 和过期时间，不读取或暴露 Cookie 值。"""
    path = Path(state_path)
    if source != "58" or not path.is_file():
        return False
    try:
        payload = load_storage_state(path)
    except (OSError, ValueError, TypeError):
        remove_storage_state(path)
        return False

    auth_names = {"id58", "PPU", "www58com", "58cooper", "passportAccount"}
    now = datetime.now(timezone.utc).timestamp()
    for cookie in payload.get("cookies", []):
        if cookie.get("name") not in auth_names or "58.com" not in (cookie.get("domain") or ""):
            continue
        expires = cookie.get("expires")
        if not expires or expires == -1:
            return True
        try:
            if float(expires) > now:
                return True
        except (TypeError, ValueError):
            continue
    remove_storage_state(path)
    return False
