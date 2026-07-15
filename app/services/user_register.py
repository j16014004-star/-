#用户注册业务逻辑层
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password
from app.crud.user_register import create_user
from app.schemas.user import UserRegister
from app.crud.user_register import user_login
from app.schemas.user import UserLogin

async def register_user(db: AsyncSession, user_data:UserRegister):
    # 调用crud层创建用户
    user = await create_user(
        db, user_data.username,
        user_data.password,
        user_data.email,
        user_data.verification_code
    )
    return user


#用户登录业务逻辑层
async def login_user(db: AsyncSession, user_data:UserLogin):
    #调用crud层登录用户
    user = await user_login(db, user_data.username)
    if user is None:
        return None
    if not verify_password(user_data.password, user.password_hash):
        return None
    return user
