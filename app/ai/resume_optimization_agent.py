'''Deterministic LangGraph resume optimization agent.'''
from __future__ import annotations

import json
import re
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai.knowledge import (
    KnowledgeChunk,
    ResumeKnowledgeRetriever,
    role_knowledge_filters,
)
from app.ai.resume_optimization_prompt import SYSTEM_PROMPT, build_user_prompt
from app.ai.tencent_maas import TencentMaaSModelGateway
from app.schemas.resume_optimization import ResumeOptimizationAIOutput


class ResumeAgentState(TypedDict, total=False):
    resume_text: str
    structured_data: dict[str, Any] | None
    request_payload: dict[str, Any]
    max_output_tokens: int | None
    retrieval_query: str
    knowledge_chunks: list[KnowledgeChunk]
    retrieval_source: str
    retrieval_error: str | None
    retrieval_audit: list[dict]
    raw_output: str
    token_usage: dict[str, int]
    used_model_name: str | None
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
        max_output_tokens: int | None = None,
    ) -> ResumeAgentState:
        return await self.graph.ainvoke(
            {
                'resume_text': resume_text,
                'structured_data': structured_data,
                'request_payload': request_payload,
                'max_output_tokens': max_output_tokens,
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
        chunks = await self.retriever.retrieve(
            state['retrieval_query'],
            filters=role_knowledge_filters(state['retrieval_query']),
        )
        return {
            'knowledge_chunks': chunks,
            'retrieval_source': getattr(self.retriever, 'last_source', 'unknown'),
            'retrieval_error': getattr(self.retriever, 'last_error', None),
            'retrieval_audit': getattr(self.retriever, 'last_results', []),
        }

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
            max_tokens=state.get('max_output_tokens'),
        )
        return {
            'raw_output': response.content,
            'token_usage': response.usage,
            'used_model_name': response.model_name,
        }

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
    candidates = [text]
    extracted = _extract_first_json_object(text)
    if extracted and extracted != text:
        candidates.append(extracted)
    last_error: json.JSONDecodeError | None = None
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
        if not isinstance(value, dict):
            raise ValueError('AI 返回内容必须是 JSON 对象')
        return value
    if _looks_truncated_json(text):
        raise ValueError('AI 返回 JSON 不完整，可能是输出 token 不足导致被截断')
    raise ValueError('AI 返回内容不是合法 JSON') from last_error


def _extract_first_json_object(text: str) -> str | None:
    start = text.find('{')
    if start < 0:
        return None
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == '\\':
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    return None


def _looks_truncated_json(text: str) -> bool:
    start = text.find('{')
    if start < 0:
        return False
    return _extract_first_json_object(text) is None


def validate_resume_facts(
    original_resume: str,
    result: ResumeOptimizationAIOutput,
) -> ResumeOptimizationAIOutput:
    normalized_source = _normalize_for_source_match(original_resume)
    source_numbers = set(_numbers(original_resume))
    optimized_numbers = set(_numbers(result.optimized_content))
    unexpected_numbers = optimized_numbers - source_numbers
    questions = list(dict.fromkeys(q.strip() for q in result.confirmation_questions if q.strip()))
    for number in sorted(unexpected_numbers, key=_number_sort_key):
        questions.append(f'请确认优化结果中新增的数字“{number}”是否真实准确，原简历未包含该数字。')

    validated_items = []
    for item in result.change_items:
        normalized_original = _normalize_for_source_match(item.original)
        if not normalized_original or normalized_original not in normalized_source:
            # The model may normalize punctuation, spaces, or quote a shortened
            # description.  A bad change annotation must not discard an otherwise
            # usable optimized resume.  Keep the generated document, omit only the
            # unverifiable annotation, and ask the user to review that section.
            questions.append(f'请核对优化后的“{item.section}”内容是否与原简历事实一致。')
            continue
        new_numbers = set(_numbers(item.optimized)) - source_numbers
        if new_numbers:
            item.requires_confirmation = True
            for number in sorted(new_numbers, key=_number_sort_key):
                questions.append(f'请确认“{item.section}”中新增的数字“{number}”是否真实准确。')
        if item.requires_confirmation and not questions:
            questions.append(f'请确认“{item.section}”中的补充信息是否准确。')
        validated_items.append(item)
    result.change_items = validated_items
    result.confirmation_questions = list(dict.fromkeys(questions))[:30]
    return result


def _compact(text: str) -> str:
    return re.sub(r'\s+', '', text or '').lower()


def _normalize_for_source_match(text: str) -> str:
    """Normalize harmless formatting differences before source verification."""
    compact = _compact(text)
    return re.sub(r'[\W_]+', '', compact, flags=re.UNICODE)


def _numbers(text: str) -> list[str]:
    text = text or ''
    numbers: list[str] = []
    date_pattern = re.compile(r'(?<!\d)((?:19|20)\d{2})[./\-年](0?[1-9]|1[0-2])月?(?!\d)')
    for match in date_pattern.finditer(text):
        year, month = match.groups()
        numbers.append(f'{year}.{int(month):02d}')
    text_without_dates = date_pattern.sub(' ', text)
    numbers.extend(re.findall(r'(?<![\d.])\d+(?:\.\d+)?%?(?![\d.])', text_without_dates))
    return numbers


def _number_sort_key(value: str) -> tuple[float, str]:
    number = value.rstrip('%')
    try:
        return (float(number), value)
    except ValueError:
        return (0.0, value)
