from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select

from app.core.security import hash_password
from app.models.user import User


async def create_user(db: AsyncSession, username: str, password: str, email: str, verification_code: str):
    #验证用户是否存在，存在返回用户None,不存在创建用户并返回用户
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user:
        return None
    else:
        #创建用户,采用hash_password方法进行密码加密
        password_hash = hash_password(password)
        new_user = User(username=username, password_hash=password_hash, email=email)
        db.add(new_user)
        await db.flush()
        await db.refresh(new_user)
        return new_user


#用户登录
async def user_login(db: AsyncSession, account: str):
    """支持用户名/邮箱/手机号登录"""
    from sqlalchemy import or_
    result = await db.execute(
        select(User).where(
            or_(
                User.username == account,
                User.email == account,
                User.phone == account
            )
        )
    )
    return result.scalar_one_or_none()
   