"""
文本处理工具
包括文本清洗和智能分块
"""
import re


def clean_text(text: str) -> str:
    """
    清洗文本

    1. 统一换行符
    2. 去除控制字符
    3. 合并多余空白
    4. 去除页眉页脚（简单规则）

    Args:
        text: 原始文本

    Returns:
        str: 清洗后的文本
    """
    if not text:
        return ""

    # 1. 统一换行符
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # 2. 去除控制字符（保留换行和制表符）
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # 3. 合并多余空白
    text = re.sub(r'[ \t]+', ' ', text)  # 合并空格和制表符
    text = re.sub(r'\n{3,}', '\n\n', text)  # 合并多余换行

    # 4. 去除页眉页脚（简单规则：连续3行相同的短文本）
    lines = text.split('\n')
    cleaned_lines = []
    prev_lines = []

    for line in lines:
        line = line.strip()
        # 跳过空行（但保留一个）
        if not line:
            if cleaned_lines and cleaned_lines[-1] != '':
                cleaned_lines.append('')
            continue

        # 检测页眉页脚（短文本重复出现）
        if len(line) < 50 and len(prev_lines) >= 2:
            if prev_lines[-1] == line and prev_lines[-2] == line:
                # 可能是页眉页脚，跳过
                continue

        cleaned_lines.append(line)
        prev_lines.append(line)
        if len(prev_lines) > 3:
            prev_lines.pop(0)

    text = '\n'.join(cleaned_lines)

    # 5. 去除首尾空白
    text = text.strip()

    return text


def split_into_chunks(
    text: str,
    min_size: int = 100,
    max_size: int = 1000,
    overlap: int = 50
) -> list[str]:
    """
    智能分块

    1. 按段落分割
    2. 合并过短的段落
    3. 分割过长的段落
    4. 添加重叠保证上下文

    Args:
        text: 清洗后的文本
        min_size: 最小块大小（字符数）
        max_size: 最大块大小（字符数）
        overlap: 重叠大小（字符数）

    Returns:
        list[str]: 分块后的文本列表
    """
    if not text:
        return []

    # 1. 按段落分割（双换行符）
    paragraphs = text.split('\n\n')
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    if not paragraphs:
        return []

    # 2. 合并过短的段落
    merged = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 < min_size:
            # 段落太短，合并到当前块
            current = current + "\n\n" + para if current else para
        else:
            # 当前块已足够，保存并开始新块
            if current:
                merged.append(current)
            current = para

    if current:
        merged.append(current)

    # 3. 分割过长的段落
    chunks = []

    for para in merged:
        if len(para) <= max_size:
            chunks.append(para)
        else:
            # 按句子分割（支持中英文）
            sentences = re.split(r'(?<=[.!?。！？])\s+', para)

            current_chunk = ""
            for sent in sentences:
                if len(current_chunk) + len(sent) + 1 > max_size and current_chunk:
                    # 当前块已满，保存
                    chunks.append(current_chunk)

                    # 添加重叠
                    if overlap > 0 and len(current_chunk) > overlap:
                        current_chunk = current_chunk[-overlap:] + " " + sent
                    else:
                        current_chunk = sent
                else:
                    current_chunk = current_chunk + " " + sent if current_chunk else sent

            if current_chunk:
                chunks.append(current_chunk)

    # 4. 过滤空块
    chunks = [c.strip() for c in chunks if c.strip()]

    return chunks
