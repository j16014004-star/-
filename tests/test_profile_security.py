import io
from types import SimpleNamespace

import pytest
from fastapi import UploadFile
from PIL import Image

from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_two_factor_token,
    decrypt_totp_secret,
    encrypt_totp_secret,
    verify_token,
)
from app.main import app
from app.services import profile_service


def test_totp_secret_is_encrypted_and_can_be_decrypted():
    secret = "JBSWY3DPEHPK3PXP"
    encrypted = encrypt_totp_secret(secret)
    assert encrypted != secret
    assert decrypt_totp_secret(encrypted) == secret


def test_tokens_have_expected_type_and_version():
    claims = {"sub": "7", "username": "tester", "ver": 3}
    assert verify_token(create_access_token(claims))["type"] == "access"
    assert verify_token(create_refresh_token(claims))["type"] == "refresh"
    second_factor = verify_token(create_two_factor_token({"sub": "7", "ver": 3}))
    assert second_factor["type"] == "two_factor"
    assert second_factor["ver"] == 3


def test_profile_routes_are_registered():
    paths = app.openapi()["paths"]
    expected = {
        "/api/auth/profile",
        "/api/auth/avatar",
        "/api/auth/password",
        "/api/auth/two-factor/setup",
        "/api/auth/two-factor/enable",
        "/api/auth/two-factor/disable",
        "/api/auth/login/two-factor",
        "/api/auth/login-logs",
        "/api/auth/preferences",
        "/api/auth/account",
    }
    assert expected <= set(paths)


@pytest.mark.asyncio
async def test_avatar_uses_api_static_url_and_is_persisted(tmp_path, monkeypatch):
    avatar_root = tmp_path / "avatars"
    monkeypatch.setattr(profile_service, "AVATAR_ROOT", avatar_root)

    image_buffer = io.BytesIO()
    Image.new("RGB", (32, 32), color=(79, 70, 229)).save(image_buffer, format="PNG")
    image_buffer.seek(0)

    class Db:
        async def flush(self):
            return None

    user = SimpleNamespace(id=7, avatar=None)
    upload = UploadFile(filename="avatar.png", file=image_buffer)
    avatar_url = await profile_service.save_avatar(Db(), user, upload)

    assert avatar_url.startswith("/api/uploads/avatars/7/avatar_")
    assert (avatar_root / "7" / avatar_url.rsplit("/", 1)[-1]).is_file()
