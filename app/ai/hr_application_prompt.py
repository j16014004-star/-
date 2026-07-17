"""Prompt for the phase-one HR application assistant."""
from __future__ import annotations

import json

from app.ai.knowledge import KnowledgeChunk


SYSTEM_PROMPT = """你是谨慎的求职投递助手。根据真实简历和岗位信息生成简短中文投递说明。
硬性规则：只能使用输入中明确存在的经历、技能和事实；不得虚构年限、业绩、学历、公司、薪资或联系方式；不得承诺用户未授权的事项；不要输出隐私数据。内容应具体、自然、80至250个汉字，说明匹配点并表达沟通意愿。
只输出合法 JSON：{"content":"投递说明","reason":"生成依据"}。"""


def build_user_prompt(
    *,
    job: dict,
    resume_text: str,
    knowledge_chunks: list[KnowledgeChunk] | None = None,
) -> str:
    safe_resume = resume_text[:12000]
    knowledge = [
        {
            "title": chunk.title,
            "section": chunk.section,
            "content": chunk.content,
        }
        for chunk in (knowledge_chunks or [])
    ]
    return (
        "请为以下岗位生成投递说明。\n岗位信息："
        + json.dumps(job, ensure_ascii=False)
        + "\n简历原文：\n"
        + safe_resume
        + "\n专业沟通规范（只作为写作规则，不能视为用户经历）：\n"
        + json.dumps(knowledge, ensure_ascii=False)
    )
