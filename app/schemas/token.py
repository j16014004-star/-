"""
Token 相关的请求/响应模型
"""
from pydantic import BaseModel, Field


class TokenRefreshRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class TokenRefreshResponse(BaseModel):
    """刷新 Token 响应"""
    access_token: str = Field(..., description="新的访问令牌")
    expires_in: int = Field(..., description="过期时间（秒）")
