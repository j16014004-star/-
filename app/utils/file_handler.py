"""
文件处理工具
包括文件验证、保存、删除
"""
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

# 允许的文件类型
ALLOWED_FILE_TYPES = {"pdf", "doc", "docx"}

# 最大文件大小（10MB）
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def validate_file(file: UploadFile) -> tuple[str, int]:
    """
    验证上传文件

    Args:
        file: 上传的文件

    Returns:
        tuple[str, int]: (文件类型, 文件大小)

    Raises:
        ValueError: 文件验证失败
    """
    if not file.filename:
        raise ValueError("文件名不能为空")

    # 获取文件扩展名
    filename_parts = file.filename.rsplit(".", 1)
    if len(filename_parts) != 2:
        raise ValueError("文件名必须包含扩展名")

    file_ext = filename_parts[1].lower()

    # 检查文件类型
    if file_ext not in ALLOWED_FILE_TYPES:
        raise ValueError(f"不支持的文件类型: {file_ext}，仅支持 {', '.join(ALLOWED_FILE_TYPES)}")

    # 读取文件内容以获取大小
    content = file.file.read()
    file_size = len(content)
    file.file.seek(0)  # 重置文件指针

    # 检查文件大小
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"文件大小超过限制: {file_size / 1024 / 1024:.2f}MB，最大支持 {MAX_FILE_SIZE / 1024 / 1024:.0f}MB")

    return file_ext, file_size


def generate_filename(user_id: int, file_ext: str) -> str:
    """
    生成唯一文件名

    格式: resume_{user_id}_{timestamp}_{uuid4_short}.{ext}

    Args:
        user_id: 用户ID
        file_ext: 文件扩展名

    Returns:
        str: 生成的文件名
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    uuid_short = uuid.uuid4().hex[:8]
    return f"resume_{user_id}_{timestamp}_{uuid_short}.{file_ext}"


def save_file(file: UploadFile, user_id: int, upload_dir: str) -> tuple[str, str, int]:
    """
    保存上传文件

    Args:
        file: 上传的文件
        user_id: 用户ID
        upload_dir: 上传目录

    Returns:
        tuple[str, str, int]: (文件名, 文件路径, 文件大小)
    """
    # 验证文件
    file_ext, file_size = validate_file(file)

    # 生成文件名
    filename = generate_filename(user_id, file_ext)

    # 创建用户目录
    user_dir = Path(upload_dir).resolve() / "resumes" / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    # 文件路径
    file_path = (user_dir / filename).resolve()

    if file_path.parent != user_dir:
        raise ValueError("无效的文件路径")

    # 保存文件
    with file_path.open("wb") as f:
        content = file.file.read()
        f.write(content)
        file.file.seek(0)

    return filename, str(file_path), file_size


def get_user_file_path(file_path: str, user_id: int, upload_dir: str) -> Path:
    """验证并返回用户简历文件的安全路径"""
    user_dir = (Path(upload_dir).resolve() / "resumes" / str(user_id)).resolve()
    resolved_path = Path(file_path).resolve()

    if resolved_path.parent != user_dir or not resolved_path.is_file():
        raise ValueError("文件不存在")

    return resolved_path


def delete_file(file_path: str, user_id: int, upload_dir: str) -> None:
    """删除用户目录中的简历文件，不存在时视为已删除"""
    user_dir = (Path(upload_dir).resolve() / "resumes" / str(user_id)).resolve()
    resolved_path = Path(file_path).resolve()

    if resolved_path.parent != user_dir:
        raise ValueError("无效的文件路径")

    if resolved_path.exists():
        if not resolved_path.is_file():
            raise ValueError("无效的文件路径")
        resolved_path.unlink()
