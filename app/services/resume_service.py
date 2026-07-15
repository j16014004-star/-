"""简历业务逻辑"""
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.resume import (
    create_chunks,
    create_resume,
    delete_resume,
    update_resume_status,
    update_resume_structured_data,
    update_resume_text,
)
from app.models.resume import Resume
from app.utils.file_handler import delete_file, save_file
from app.utils.text_extractor import extract_text
from app.utils.text_processor import clean_text, split_into_chunks
from app.utils.resume_parser import parse_resume


async def upload_resume(
    db: AsyncSession,
    user_id: int,
    file: UploadFile,
    title: str | None = None,
) -> Resume:
    """保存、提取、清洗并分块简历文件"""
    normalized_title = title.strip() if title else None
    if normalized_title == "":
        normalized_title = None
    if normalized_title and len(normalized_title) > 200:
        raise ValueError("简历标题不能超过200个字符")

    filename, file_path, file_size = save_file(file, user_id, settings.UPLOAD_DIR)
    file_type = filename.rsplit(".", 1)[1]

    try:
        resume = await create_resume(
            db=db,
            user_id=user_id,
            file_type=file_type,
            file_path=file_path,
            file_size=file_size,
            title=normalized_title,
        )
    except Exception:
        delete_file(file_path, user_id, settings.UPLOAD_DIR)
        raise

    await update_resume_status(db, resume.id, "processing")

    try:
        extracted_text = extract_text(file_path, file_type)
        cleaned_text = clean_text(extracted_text)

        # 结构化解析（独立隔离，失败不阻断上传）
        structured_data = None
        try:
            structured_data = parse_resume(cleaned_text)
        except Exception:
            structured_data = {
                "parser_version": "rules-v1",
                "basic_info": {"name": None, "phone": [], "email": [],
                               "location": None, "links": []},
                "education": [],
                "work_experience": [],
                "projects": [],
                "skills": [],
                "warnings": ["parser_unexpected_error"],
            }

        chunks = split_into_chunks(cleaned_text)

        await update_resume_text(db, resume.id, cleaned_text)
        await update_resume_structured_data(db, resume.id, structured_data)
        await create_chunks(db, resume.id, chunks)
        await update_resume_status(db, resume.id, "completed")
    except Exception as exc:
        await update_resume_status(db, resume.id, "failed", str(exc)[:500])

    await db.refresh(resume)
    return resume


async def remove_resume(
    db: AsyncSession,
    resume: Resume,
    user_id: int,
) -> None:
    """删除简历的本地文件与数据库记录"""
    delete_file(resume.file_path, user_id, settings.UPLOAD_DIR)
    await delete_resume(db, resume.id, user_id)
