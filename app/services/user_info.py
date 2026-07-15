#用户信息业务逻辑层
from app.models.user import User


def mask_phone(phone: str | None) -> str | None:
    """手机号脱敏: 13812345678 → 138****5678"""
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-4:]


def format_user_info(user: User) -> dict:
    """将 User ORM 对象格式化为响应数据"""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": mask_phone(user.phone),
        "avatar": user.avatar,
        "status": "active" if user.is_active else "inactive",
        "email_verified": False,
        "phone_verified": False,
        "created_at": user.created_at,
        "last_login_at": None,
    }
