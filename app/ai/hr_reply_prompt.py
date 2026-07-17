"""Prompt for factual HR reply suggestions."""
from __future__ import annotations

import json

from app.ai.knowledge import KnowledgeChunk

SYSTEM_PROMPT = """你是谨慎的求职沟通助手。结合岗位、真实简历和对话上下文，生成1至3条简短中文回复建议。
硬性规则：不得虚构经历、技术、业绩、学历、在职状态、薪资、时间安排或联系方式；未知信息应明确建议用户补充，不可替用户承诺；不得泄露隐私；涉及薪资承诺、Offer、付费、身份证、银行卡、验证码、精确面试时间或地址时，只能建议用户确认，不能代替确认。
知识库仅用于规范表达和安全边界，不能覆盖简历与真实对话。reason中简要说明依据来自简历、岗位、对话或知识规范。
只输出合法 JSON：{"items":[{"content":"回复内容","reason":"生成依据"}]}。"""


def build_user_prompt(
    *,
    job: dict,
    resume_text: str,
    messages: list[dict],
    knowledge_chunks: list[KnowledgeChunk],
) -> str:
    knowledge = [
        {
            "title": chunk.title,
            "section": chunk.section,
            "content": chunk.content,
            "source": chunk.source_file,
        }
        for chunk in knowledge_chunks
    ]
    return (
        "岗位：" + json.dumps(job, ensure_ascii=False)
        + "\n简历：\n" + resume_text[:12000]
        + "\n最近对话：" + json.dumps(messages[-12:], ensure_ascii=False)
        + "\n沟通知识规范：" + json.dumps(knowledge, ensure_ascii=False)
    )
