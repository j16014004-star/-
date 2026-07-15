"""
文本提取工具
支持 PDF、DOC、DOCX 格式
"""
import os


def extract_text_from_pdf(file_path: str) -> str:
    """从 PDF 文件中提取文本"""
    import pdfplumber

    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    return "\n\n".join(text_parts)


def extract_text_from_docx(file_path: str) -> str:
    """从 DOCX 文件中提取文本"""
    from docx import Document

    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def extract_text(file_path: str, file_type: str) -> str:
    """
    从文件中提取文本

    Args:
        file_path: 文件路径
        file_type: 文件类型 (pdf/doc/docx)

    Returns:
        str: 提取的文本

    Raises:
        ValueError: 不支持的文件类型
    """
    file_type = file_type.lower()

    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "docx":
        return extract_text_from_docx(file_path)
    elif file_type == "doc":
        # .doc 格式较旧，尝试用 docx 方式读取
        try:
            return extract_text_from_docx(file_path)
        except Exception:
            raise ValueError(f"不支持的 .doc 文件格式，请转换为 .docx 后上传")
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")
