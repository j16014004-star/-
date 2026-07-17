"""简历路由"""
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.crud.resume import get_resume_by_id, get_user_resumes
from app.models.resume import Resume
from app.models.user import User
from app.services.resume_service import remove_resume, upload_resume
from app.services.job_refresh_service import trigger_refresh_for_new_resume
from app.utils.file_handler import get_user_file_path
from app.utils.resume_parser import normalize_structured_data_for_frontend

router = APIRouter(prefix="/api/resumes", tags=["简历"])

MIME_TYPES = {
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def resume_file_url(resume: Resume) -> str:
    return f"/api/resumes/{resume.id}/download"


def serialize_resume(resume: Resume, include_detail: bool = False) -> dict:
    data = {
        "id": resume.id,
        "user_id": resume.user_id,
        "title": resume.title,
        "file_type": resume.file_type,
        "file_url": resume_file_url(resume),
        "file_size": resume.file_size,
        "score": None,
        "status": resume.status,
        "analysis": None,
        "error_message": resume.error_message,
        "created_at": resume.created_at,
        "updated_at": resume.updated_at,
    }
    if include_detail:
        structured_data = normalize_structured_data_for_frontend(resume.structured_data)
        data["extracted_text"] = resume.extracted_text
        data["raw_text"] = resume.extracted_text
        data["text"] = resume.extracted_text
        data["parsed_text"] = resume.extracted_text
        data["structured_data"] = structured_data
        data["structured_content"] = structured_data
        data["parsed_content"] = structured_data
        data["resume_content"] = structured_data
        data["content"] = {
            **structured_data,
            "extracted_text": resume.extracted_text,
            "raw_text": resume.extracted_text,
            "text": resume.extracted_text,
            "parsed_text": resume.extracted_text,
        }
        data["chunks"] = [
            {
                "id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "char_count": chunk.char_count,
                "metadata": {"source": "resume"},
                "created_at": chunk.created_at,
            }
            for chunk in sorted(resume.chunks, key=lambda item: item.chunk_index)
        ]
    return data


async def get_owned_resume_or_404(
    db: AsyncSession,
    resume_id: int,
    user_id: int,
) -> Resume:
    resume = await get_resume_by_id(db, resume_id, user_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="简历不存在")
    return resume


@router.post("/upload")
async def upload_resume_file(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传、清洗并保存简历"""
    try:
        resume = await upload_resume(db, current_user.id, file, title)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    recommendation_refresh = None
    if resume.status == "completed":
        recommendation_refresh = await trigger_refresh_for_new_resume(
            db, user_id=current_user.id, resume=resume,
        )

    data = serialize_resume(resume)
    data["recommendation_refresh"] = recommendation_refresh
    return {
        "code": 200,
        "message": "上传成功",
        "data": data,
    }


@router.get("")
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的简历列表"""
    resumes = await get_user_resumes(db, current_user.id)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [serialize_resume(resume) for resume in resumes],
            "total": len(resumes),
            "page": 1,
            "page_size": len(resumes),
        },
    }


@router.get("/{resume_id}")
async def get_resume_detail(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取简历详情和已清洗的文本分块"""
    resume = await get_owned_resume_or_404(db, resume_id, current_user.id)
    return {
        "code": 200,
        "message": "success",
        "data": serialize_resume(resume, include_detail=True),
    }


@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """下载当前用户拥有的原始简历文件"""
    resume = await get_owned_resume_or_404(db, resume_id, current_user.id)
    try:
        file_path = get_user_file_path(resume.file_path, current_user.id, settings.UPLOAD_DIR)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="简历文件不存在") from exc

    return FileResponse(
        path=file_path,
        media_type=MIME_TYPES[resume.file_type],
        filename=Path(file_path).name,
    )


@router.delete("/{resume_id}")
async def delete_resume_file(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除当前用户的简历、分块及本地原始文件"""
    resume = await get_owned_resume_or_404(db, resume_id, current_user.id)
    try:
        await remove_resume(db, resume, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "code": 200,
        "message": "删除成功",
        "data": None,
    }
