'''Deterministic LangGraph resume optimization agent.'''
from __future__ import annotations

import json
import re
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai.knowledge import KnowledgeChunk, ResumeKnowledgeRetriever
from app.ai.resume_optimization_prompt import SYSTEM_PROMPT, build_user_prompt
from app.ai.tencent_maas import TencentMaaSModelGateway
from app.schemas.resume_optimization import ResumeOptimizationAIOutput


class ResumeAgentState(TypedDict, total=False):
    resume_text: str
    structured_data: dict[str, Any] | None
    request_payload: dict[str, Any]
    retrieval_query: str
    knowledge_chunks: list[KnowledgeChunk]
    raw_output: str
    token_usage: dict[str, int]
    result: ResumeOptimizationAIOutput


class ResumeOptimizationAgent:
    def __init__(
        self,
        *,
        gateway: TencentMaaSModelGateway | None = None,
        retriever: ResumeKnowledgeRetriever | None = None,
    ) -> None:
        self.gateway = gateway or TencentMaaSModelGateway()
        self.retriever = retriever or ResumeKnowledgeRetriever(self.gateway)
        graph = StateGraph(ResumeAgentState)
        graph.add_node('analyze_context', self._analyze_context)
        graph.add_node('retrieve_knowledge', self._retrieve_knowledge)
        graph.add_node('generate', self._generate)
        graph.add_node('validate', self._validate)
        graph.add_edge(START, 'analyze_context')
        graph.add_edge('analyze_context', 'retrieve_knowledge')
        graph.add_edge('retrieve_knowledge', 'generate')
        graph.add_edge('generate', 'validate')
        graph.add_edge('validate', END)
        self.graph = graph.compile()

    async def run(
        self,
        *,
        resume_text: str,
        structured_data: dict | None,
        request_payload: dict[str, Any],
    ) -> ResumeAgentState:
        return await self.graph.ainvoke(
            {
                'resume_text': resume_text,
                'structured_data': structured_data,
                'request_payload': request_payload,
            }
        )

    @staticmethod
    async def _analyze_context(state: ResumeAgentState) -> dict[str, Any]:
        payload = state['request_payload']
        focus = '、'.join(payload.get('optimization_focus') or ['all'])
        role = payload.get('target_role') or '通用岗位'
        style = payload.get('style') or 'professional'
        query = f'{role} 中文简历 {focus} {style} ATS STAR 真实性 优化规则'
        return {'retrieval_query': query}

    async def _retrieve_knowledge(self, state: ResumeAgentState) -> dict[str, Any]:
        chunks = await self.retriever.retrieve(state['retrieval_query'])
        return {'knowledge_chunks': chunks}

    async def _generate(self, state: ResumeAgentState) -> dict[str, Any]:
        prompt = build_user_prompt(
            resume_text=state['resume_text'],
            structured_data=state.get('structured_data'),
            request_payload=state['request_payload'],
            knowledge_chunks=state.get('knowledge_chunks') or [],
        )
        response = await self.gateway.generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
        )
        return {'raw_output': response.content, 'token_usage': response.usage}

    @staticmethod
    async def _validate(state: ResumeAgentState) -> dict[str, Any]:
        payload = _parse_json_object(state['raw_output'])
        result = ResumeOptimizationAIOutput.model_validate(payload)
        result = validate_resume_facts(state['resume_text'], result)
        return {'result': result}


def _parse_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*```$', '', text)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError('AI 返回内容不是合法 JSON') from exc
    if not isinstance(value, dict):
        raise ValueError('AI 返回内容必须是 JSON 对象')
    return value


def validate_resume_facts(
    original_resume: str,
    result: ResumeOptimizationAIOutput,
) -> ResumeOptimizationAIOutput:
    normalized_source = _compact(original_resume)
    source_numbers = set(_numbers(original_resume))
    optimized_numbers = set(_numbers(result.optimized_content))
    unexpected_numbers = optimized_numbers - source_numbers
    if unexpected_numbers:
        raise ValueError('优化结果包含原简历不存在的数字，已阻止保存')

    questions = list(dict.fromkeys(q.strip() for q in result.confirmation_questions if q.strip()))
    validated_items = []
    for item in result.change_items:
        normalized_original = _compact(item.original)
        if not normalized_original or normalized_original not in normalized_source:
            raise ValueError('修改项原文无法在原简历中找到')
        new_numbers = set(_numbers(item.optimized)) - source_numbers
        if new_numbers:
            raise ValueError('修改项包含原简历不存在的数字，已阻止保存')
        if item.requires_confirmation and not questions:
            questions.append(f'请确认“{item.section}”中的补充信息是否准确。')
        validated_items.append(item)
    result.change_items = validated_items
    result.confirmation_questions = questions
    return result


def _compact(text: str) -> str:
    return re.sub(r'\s+', '', text or '').lower()


def _numbers(text: str) -> list[str]:
    return re.findall(r'(?<!\d)\d+(?:\.\d+)?%?', text or '')
