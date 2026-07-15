import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.ai.knowledge import KnowledgeChunk, load_knowledge_chunks
from app.ai.resume_optimization_agent import ResumeOptimizationAgent, validate_resume_facts
from app.ai.tencent_maas import TextGenerationResult
from app.schemas.resume_optimization import (
    ResumeChangeItem,
    ResumeOptimizationAIOutput,
    ResumeOptimizationRequest,
)
from app.services.resume_optimization_service import build_input_hash


def test_target_role_is_required():
    with pytest.raises(ValidationError):
        ResumeOptimizationRequest(
            optimization_type='target_role',
            optimization_focus=['ats'],
            style='professional',
            preserve_structure=True,
        )


def test_all_focus_cannot_be_combined():
    with pytest.raises(ValidationError):
        ResumeOptimizationRequest(
            optimization_type='general',
            optimization_focus=['all', 'skills'],
            style='professional',
            preserve_structure=True,
        )


def test_input_hash_is_stable():
    payload = {
        'optimization_type': 'general',
        'target_role': None,
        'optimization_focus': ['all'],
        'style': 'professional',
        'preserve_structure': True,
        'analysis_id': None,
    }
    first = build_input_hash(user_id=1, resume_id=2, resume_text='Python开发', payload=payload)
    second = build_input_hash(user_id=1, resume_id=2, resume_text='Python开发', payload=payload)
    assert first == second
    assert len(first) == 64


def test_knowledge_document_is_chunked():
    chunks = load_knowledge_chunks(Path('knowledge_base/resume_optimization/source'))
    assert chunks
    assert all(chunk.content for chunk in chunks)
    assert all(len(chunk.content) <= 800 for chunk in chunks)


def test_fact_guard_rejects_new_numbers():
    output = ResumeOptimizationAIOutput(
        optimization_summary='优化项目描述',
        optimized_content='使用FastAPI开发接口，性能提升50%。',
        score_improvement=20,
        change_items=[
            ResumeChangeItem(
                section='项目经历',
                original='使用FastAPI开发接口。',
                optimized='使用FastAPI开发接口，性能提升50%。',
                reason='补充成果',
                evidence='原文只说明使用FastAPI开发接口。',
                requires_confirmation=False,
            )
        ],
        confirmation_questions=[],
    )
    with pytest.raises(ValueError, match='不存在的数字'):
        validate_resume_facts('使用FastAPI开发接口。', output)


def test_fact_guard_accepts_evidence_based_rewrite():
    output = ResumeOptimizationAIOutput(
        optimization_summary='优化项目描述',
        optimized_content='使用FastAPI实现业务接口和参数校验。',
        score_improvement=15,
        change_items=[
            ResumeChangeItem(
                section='项目经历',
                original='使用FastAPI开发接口。',
                optimized='使用FastAPI实现业务接口和参数校验。',
                reason='将描述改为具体技术动作',
                evidence='原文包含使用FastAPI开发接口。',
                requires_confirmation=False,
            )
        ],
        confirmation_questions=[],
    )
    result = validate_resume_facts('使用FastAPI开发接口。', output)
    assert result.optimized_content.startswith('使用FastAPI')


class FakeGateway:
    async def generate_json(self, *, system_prompt: str, user_prompt: str):
        assert '不得虚构' in system_prompt
        assert '<resume_data>' in user_prompt
        payload = {
            'optimization_summary': '优化了项目表达',
            'optimized_content': '使用FastAPI实现业务接口和参数校验。',
            'score_improvement': 15,
            'change_items': [
                {
                    'section': '项目经历',
                    'original': '使用FastAPI开发接口。',
                    'optimized': '使用FastAPI实现业务接口和参数校验。',
                    'reason': '描述更具体',
                    'evidence': '原文包含FastAPI接口开发',
                    'requires_confirmation': False,
                }
            ],
            'confirmation_questions': [],
        }
        return TextGenerationResult(content=json.dumps(payload, ensure_ascii=False), usage={'total_tokens': 30})


class FakeRetriever:
    async def retrieve(self, query: str, *, top_k: int | None = None):
        assert '简历' in query
        return [
            KnowledgeChunk(
                id='chunk-1',
                document_id='doc-1',
                title='简历规则',
                section='项目经历',
                content='项目描述应使用真实技术动作。',
                source_file='rules.md',
                version='v1',
            )
        ]


@pytest.mark.asyncio
async def test_agent_runs_without_real_cloud_call():
    agent = ResumeOptimizationAgent(gateway=FakeGateway(), retriever=FakeRetriever())
    state = await agent.run(
        resume_text='使用FastAPI开发接口。',
        structured_data={'skills': ['FastAPI']},
        request_payload={
            'optimization_type': 'general',
            'target_role': None,
            'optimization_focus': ['project_experience'],
            'style': 'technical',
            'preserve_structure': True,
            'analysis_id': None,
        },
    )
    assert state['result'].optimization_summary == '优化了项目表达'
    assert state['token_usage']['total_tokens'] == 30
