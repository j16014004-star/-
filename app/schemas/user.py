from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


#注册验证
class UserRegister(BaseModel):
    username: str=Field(...,min_length=2,max_length=12)
    password: str=Field(...,min_length=6,max_length=64)
    email: EmailStr
    verification_code: str | None = None


#登录验证
class UserLogin(BaseModel):
    username: str=Field(...,min_length=2,max_length=100)
    password: str=Field(...,min_length=6,max_length=64)


class TwoFactorLogin(BaseModel):
    two_factor_token: str
    code: str = Field(..., min_length=6, max_length=12)



#用户信息验证
class UserInfo(BaseModel):
    id: int
    username: str
    email: EmailStr
    phone: str|None
    avatar: str | None 
    status: str
    email_verified: bool
    phone_verified: bool
    two_factor_enabled: bool
    created_at: datetime
    last_login_at: datetime|None

    class Config:
        from_attributes = True
