"""
简历 CRUD 操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.models.resume import Resume, ResumeChunk


async def create_resume(
    db: AsyncSession,
    user_id: int,
    file_type: str,
    file_path: str,
    file_size: int,
    title: str | None = None,
) -> Resume:
    """
    创建简历记录

    Args:
        db: 数据库会话
        user_id: 用户ID
        file_type: 文件类型
        file_path: 文件路径
        file_size: 文件大小
        title: 简历标题

    Returns:
        Resume: 创建的简历对象
    """
    resume = Resume(
        user_id=user_id,
        title=title,
        file_type=file_type,
        file_path=file_path,
        file_size=file_size,
        status="pending",
    )
    db.add(resume)
    await db.flush()
    await db.refresh(resume)
    return resume


async def update_resume_text(
    db: AsyncSession,
    resume_id: int,
    extracted_text: str,
) -> None:
    """
    更新简历提取的文本

    Args:
        db: 数据库会话
        resume_id: 简历ID
        extracted_text: 提取的文本
    """
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if resume:
        resume.extracted_text = extracted_text
        resume.status = "processing"
        await db.flush()


async def update_resume_status(
    db: AsyncSession,
    resume_id: int,
    status: str,
    error_message: str | None = None,
) -> None:
    """
    更新简历状态

    Args:
        db: 数据库会话
        resume_id: 简历ID
        status: 状态
        error_message: 错误信息
    """
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if resume:
        resume.status = status
        resume.error_message = error_message
        await db.flush()


async def create_chunks(
    db: AsyncSession,
    resume_id: int,
    chunks: list[str],
) -> list[ResumeChunk]:
    """
    批量创建简历分块

    Args:
        db: 数据库会话
        resume_id: 简历ID
        chunks: 分块文本列表

    Returns:
        list[ResumeChunk]: 创建的分块对象列表
    """
    chunk_objects = []
    for idx, content in enumerate(chunks):
        chunk = ResumeChunk(
            resume_id=resume_id,
            chunk_index=idx,
            content=content,
            char_count=len(content),
        )
        db.add(chunk)
        chunk_objects.append(chunk)

    await db.flush()
    return chunk_objects


async def get_resume_by_id(
    db: AsyncSession,
    resume_id: int,
    user_id: int | None = None,
) -> Resume | None:
    """
    根据ID获取简历（包含分块）

    Args:
        db: 数据库会话
        resume_id: 简历ID
        user_id: 用户ID（用于权限验证）

    Returns:
        Resume | None: 简历对象
    """
    query = select(Resume).options(selectinload(Resume.chunks)).where(Resume.id == resume_id)

    if user_id is not None:
        query = query.where(Resume.user_id == user_id)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_user_resumes(
    db: AsyncSession,
    user_id: int,
) -> list[Resume]:
    """
    获取用户的所有简历

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        list[Resume]: 简历列表
    """
    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
    )
    return list(result.scalars().all())


async def update_resume_structured_data(
    db: AsyncSession,
    resume_id: int,
    structured_data: dict,
) -> None:
    """
    更新简历结构化解析结果

    Args:
        db: 数据库会话
        resume_id: 简历ID
        structured_data: 结构化解析数据
    """
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if resume:
        resume.structured_data = structured_data
        await db.flush()


async def delete_resume(
    db: AsyncSession,
    resume_id: int,
    user_id: int,
) -> bool:
    """
    删除简历（同时删除分块）

    Args:
        db: 数据库会话
        resume_id: 简历ID
        user_id: 用户ID（用于权限验证）

    Returns:
        bool: 是否删除成功
    """
    # 先查询简历是否存在且属于该用户
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
    )
    resume = result.scalar_one_or_none()

    if not resume:
        return False

    # 删除简历（级联删除分块）
    await db.delete(resume)
    await db.flush()
    return True
