import bcrypt
import base64
import hashlib
import uuid
from cryptography.fernet import Fernet
from jose import jwt
from datetime import datetime, timedelta, timezone

from app.core.config import settings

def hash_password(password: str) -> str:
    """
    密码加密
    明文密码 -> bcrypt哈希
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """
    验证密码
    用户输入密码
    对比数据库中的hash
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


#jwt token生成和验证
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

#创建token函数
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc).timestamp()
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

#创建refresh token函数
def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.now(timezone.utc).timestamp(),
        "jti": str(uuid.uuid4())
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_two_factor_token(data: dict) -> str:
    payload = data.copy()
    payload.update({
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        "type": "two_factor",
        "iat": datetime.now(timezone.utc).timestamp(),
        "jti": str(uuid.uuid4()),
    })
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

#验证token函数
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        return None


def encrypt_totp_secret(secret: str) -> str:
    key = settings.TOTP_ENCRYPTION_KEY.encode() if settings.TOTP_ENCRYPTION_KEY else base64.urlsafe_b64encode(
        hashlib.sha256((settings.JWT_SECRET_KEY + ":totp").encode()).digest()
    )
    return Fernet(key).encrypt(secret.encode()).decode()


def decrypt_totp_secret(value: str) -> str:
    key = settings.TOTP_ENCRYPTION_KEY.encode() if settings.TOTP_ENCRYPTION_KEY else base64.urlsafe_b64encode(
        hashlib.sha256((settings.JWT_SECRET_KEY + ":totp").encode()).digest()
    )
    return Fernet(key).decrypt(value.encode()).decode()
