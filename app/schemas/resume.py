"""
简历相关的 Pydantic 模型
"""
from datetime import datetime

from pydantic import BaseModel, Field


class ResumeUpload(BaseModel):
    """简历上传请求"""
    title: str | None = Field(None, description="简历标题")


class ResumeChunkResponse(BaseModel):
    """简历分块响应"""
    id: int
    chunk_index: int
    content: str
    char_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeResponse(BaseModel):
    """简历响应"""
    id: int
    user_id: int
    title: str | None
    file_type: str
    file_url: str
    file_size: int
    score: int | None = None
    status: str
    analysis: dict | None = None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeDetailResponse(ResumeResponse):
    """简历详情响应（包含分块与结构化解析）"""
    extracted_text: str | None
    chunks: list[ResumeChunkResponse] = Field(default_factory=list)
    structured_data: dict | None = None

    class Config:
        from_attributes = True
