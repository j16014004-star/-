import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.ai.knowledge import KnowledgeChunk, load_knowledge_chunks
from app.ai.resume_optimization_agent import (
    ResumeOptimizationAgent,
    _parse_json_object,
    validate_resume_facts,
)
from app.ai.tencent_maas import TextGenerationResult
from app.schemas.resume_optimization import (
    ConfirmationAIApplyRequest,
    ManualConfirmationItem,
    ResumeChangeItem,
    ResumeOptimizationAIOutput,
    ResumeOptimizationRequest,
)
from app.services.resume_optimization_service import build_input_hash
from app.utils.resume_parser import normalize_structured_data_for_frontend


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


def test_ai_confirmation_request_validates_confirmed_answers():
    body = ConfirmationAIApplyRequest(
        optimized_content='当前优化简历',
        confirmation_questions=['请确认数据库类型'],
        confirmed_answers=[{
            'question': '请确认数据库类型',
            'answer': '使用 MySQL 数据库',
        }],
    )
    assert body.confirmed_answers[0].answer == '使用 MySQL 数据库'
    with pytest.raises(ValidationError, match='必须存在于 confirmation_questions'):
        ConfirmationAIApplyRequest(
            optimized_content='当前优化简历',
            confirmation_questions=['请确认数据库类型'],
            confirmed_answers=[{
                'question': '请确认项目链接',
                'answer': 'https://example.com',
            }],
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


def test_structured_resume_data_has_frontend_aliases():
    structured = normalize_structured_data_for_frontend({
        'basic_info': {
            'name': '张三',
            'phone': ['13800138000'],
            'email': ['demo@example.com'],
            'location': '西安',
        },
        'education': [
            {
                'school': '天津大学',
                'major': '信息管理与信息系统',
                'degree': '本科',
                'start_date': '2019-09',
                'end_date': '2023-07',
            }
        ],
        'work_experience': [
            {
                'company': '陕西通运汽车物流有限公司',
                'title': '数据分析专员',
                'start_date': '2024-04',
                'end_date': '2024-11',
                'description': '负责物流业务数据维护。',
            }
        ],
        'skills': ['Python', 'MySQL'],
    })
    assert structured['name'] == '张三'
    assert structured['phone'] == '13800138000'
    assert structured['education_list'][0]['period'] == '2019.09 - 2023.07'
    assert structured['work_list'][0]['position'] == '数据分析专员'
    assert structured['skills'] == ['Python', 'MySQL']


def test_fact_guard_marks_new_numbers_for_confirmation():
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
    result = validate_resume_facts('使用FastAPI开发接口。', output)

    assert result.change_items[0].requires_confirmation is True
    assert any('50%' in question for question in result.confirmation_questions)


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


def test_fact_guard_does_not_flag_date_separator_changes():
    output = ResumeOptimizationAIOutput(
        optimization_summary='优化教育经历日期格式',
        optimized_content='天津大学 本科 2019.09 - 2023.07',
        score_improvement=80,
        change_items=[
            ResumeChangeItem(
                section='教育经历',
                original='天津大学 本科 2019-09 - 2023-07',
                optimized='天津大学 本科 2019.09 - 2023.07',
                reason='统一日期格式',
                evidence='原文包含对应起止日期',
                requires_confirmation=False,
            )
        ],
        confirmation_questions=[],
    )
    result = validate_resume_facts('天津大学 本科 2019-09 - 2023-07', output)

    assert result.confirmation_questions == []
    assert result.change_items[0].requires_confirmation is False


def test_fact_guard_accepts_harmless_punctuation_and_spacing_changes():
    output = ResumeOptimizationAIOutput(
        optimization_summary='优化项目描述',
        optimized_content='使用 FastAPI、MySQL 完成接口开发。',
        score_improvement=12,
        change_items=[
            ResumeChangeItem(
                section='项目经历',
                original='使用 FastAPI / MySQL，完成接口开发',
                optimized='使用 FastAPI、MySQL 完成接口开发。',
                reason='统一表达格式',
                evidence='来自项目经历原文',
                requires_confirmation=False,
            )
        ],
        confirmation_questions=[],
    )

    result = validate_resume_facts('使用FastAPI、MySQL完成接口开发。', output)

    assert len(result.change_items) == 1
    assert result.confirmation_questions == []


def test_fact_guard_drops_only_unverifiable_change_item_instead_of_failing_task():
    output = ResumeOptimizationAIOutput(
        optimization_summary='优化项目描述',
        optimized_content='使用 FastAPI 完成业务接口开发。',
        score_improvement=10,
        change_items=[
            ResumeChangeItem(
                section='项目经历',
                original='原简历中不存在的描述',
                optimized='使用 FastAPI 完成业务接口开发。',
                reason='优化表达',
                evidence='模型生成的修改说明',
                requires_confirmation=False,
            )
        ],
        confirmation_questions=[],
    )

    result = validate_resume_facts('使用 FastAPI 开发接口。', output)

    assert result.optimized_content == '使用 FastAPI 完成业务接口开发。'
    assert result.change_items == []
    assert result.confirmation_questions == ['请核对优化后的“项目经历”内容是否与原简历事实一致。']


def test_parse_json_object_accepts_wrapped_json():
    payload = {'optimization_summary': 'ok', 'score_improvement': 10}
    raw = f'下面是优化结果：\n{json.dumps(payload, ensure_ascii=False)}\n请查收。'
    assert _parse_json_object(raw) == payload


def test_parse_json_object_reports_truncated_json():
    with pytest.raises(ValueError, match='JSON 不完整'):
        _parse_json_object('{"optimization_summary":"ok","optimized_content":"未结束')


def test_extract_added_content_has_safe_fallback():
    from app.routers.resume_optimizations import (
        build_pending_confirmation_summary,
        derive_actual_added_content,
        extract_added_content,
        merge_change_items,
        merge_confirmation_actions,
        missing_confirmation_content,
        serialize_confirmation_preview,
        split_redundant_date_questions,
    )

    added = extract_added_content('第一行', '第一行\n第二行', '已调整')
    assert added == '第二行'
    assert extract_added_content('第一行', '第一行', '已调整') == '已调整'
    preview = serialize_confirmation_preview(
        optimized_content='原内容',
        added_content='',
        summary='处理说明',
    )
    assert preview['added_content'] == '处理说明'
    assert '需要用户确认' in build_pending_confirmation_summary(['请确认使用的 Python 库'])
    kept, skipped = split_redundant_date_questions(
        ['请确认优化结果中新增的数字“2019.09”是否真实准确', '请确认优化结果中新增的数字“50%”是否真实准确'],
        '天津大学 本科 2019-09 - 2023-07',
    )
    assert skipped == ['请确认优化结果中新增的数字“2019.09”是否真实准确']
    assert kept == ['请确认优化结果中新增的数字“50%”是否真实准确']
    original_change = {
        'section': '项目经历',
        'original': '开发接口',
        'optimized': '使用 FastAPI 开发接口',
        'reason': '补充技术关键词',
        'evidence': '原文包含接口开发',
    }
    confirmation_change = {
        'section': '用户确认补充',
        'original': '使用了哪些数据库？',
        'optimized': '使用 MySQL 数据库',
        'reason': '用户确认后补充',
        'evidence': '来自用户回答',
    }
    assert merge_change_items([original_change], [original_change, confirmation_change]) == [
        {**original_change, 'evidence_source': 'original_resume', 'requires_confirmation': False},
        {**confirmation_change, 'evidence_source': 'original_resume', 'requires_confirmation': False},
    ]
    action = {'type': 'manual', 'created_at': '2026-07-16 10:00', 'added_content': 'MySQL'}
    assert merge_confirmation_actions([action], [action]) == [action]
    confirmed_change = {
        **confirmation_change,
        'evidence_source': 'user_confirmation',
    }
    final_content = '技能：Python\n使用 MySQL 数据库'
    assert derive_actual_added_content(
        '技能：Python',
        final_content,
        [confirmed_change],
        evidence_source='user_confirmation',
    ) == '使用 MySQL 数据库'
    assert missing_confirmation_content(final_content, [confirmed_change]) == []
    assert missing_confirmation_content('技能：Python', [confirmed_change]) == ['使用 MySQL 数据库']
    confirmed_action = {
        'type': 'ai',
        'added_content': '使用 MySQL 数据库',
    }
    assert missing_confirmation_content(final_content, [], [confirmed_action]) == []
    assert missing_confirmation_content('技能：Python', [], [confirmed_action]) == ['使用 MySQL 数据库']


def test_saved_serializer_always_returns_full_original_content():
    from types import SimpleNamespace

    from app.routers.resume_optimizations import serialize_optimization_version

    version = SimpleNamespace(
        id=1,
        resume_id=2,
        title='测试简历-优化简历',
        is_saved=True,
        saved_at=None,
        optimization_summary='已优化',
        original_content='完整原始简历\n第二行',
        optimized_content='完整优化简历',
        score_improvement=80,
        change_items=[{
            'section': '经历',
            'original': '第一条原文',
            'optimized': '第一条优化',
        }],
        confirmation_questions=[],
        confirmation_actions=[],
        created_at=None,
    )
    result = serialize_optimization_version(version)
    assert result['original_content'] == '完整原始简历\n第二行'
    assert result['original'] == '完整原始简历\n第二行'


@pytest.mark.asyncio
async def test_delete_saved_optimization_is_idempotent(monkeypatch):
    from types import SimpleNamespace

    from app.routers import resume_optimizations

    async def get_missing_version(*_args, **_kwargs):
        return None

    monkeypatch.setattr(
        resume_optimizations,
        'get_owned_saved_optimization_version',
        get_missing_version,
    )
    result = await resume_optimizations.delete_saved_resume_optimization(
        saved_optimization_id=999,
        current_user=SimpleNamespace(id=1),
        db=SimpleNamespace(),
    )
    assert result == {
        'code': 200,
        'message': '优化简历已删除或不存在',
        'data': None,
    }


def test_confirmed_answer_fallback_always_adds_user_content():
    from app.routers.resume_optimizations import build_confirmed_answer_fallback

    payload = build_confirmed_answer_fallback(
        '技能：Python',
        [ManualConfirmationItem(question='请确认数据库类型', answer='使用 MySQL 数据库')],
        ['请确认数据库类型', '请确认项目链接'],
        80,
    )
    assert '使用 MySQL 数据库' in payload['optimized_content']
    assert payload['resolved_questions'] == ['请确认数据库类型']
    assert payload['remaining_questions'] == ['请确认项目链接']
    assert payload['change_items'][0]['evidence_source'] == 'user_confirmation'


def test_prompt_engineering_separates_facts_from_knowledge_rules():
    from app.ai.resume_optimization_prompt import (
        CONFIRMATION_SYSTEM_PROMPT,
        SYSTEM_PROMPT,
        build_confirmation_prompt,
        build_user_prompt,
    )

    chunk = KnowledgeChunk(
        id='rule-1',
        document_id='doc-1',
        title='优化规则',
        section='ATS',
        content='使用清晰的岗位关键词。',
        source_file='rules.md',
        version='v1',
    )
    prompt = build_user_prompt(
        resume_text='使用 FastAPI 开发接口。',
        structured_data={'skills': ['FastAPI']},
        request_payload={'optimization_type': 'general'},
        knowledge_chunks=[chunk],
    )
    assert 'knowledge 只影响怎么写，不能决定写什么事实' in SYSTEM_PROMPT
    assert 'evidence_source' in SYSTEM_PROMPT
    assert '<task_instruction>' in prompt
    assert 'rule-1' in prompt

    confirmation_prompt = build_confirmation_prompt(
        optimized_content='使用 FastAPI 开发接口。',
        original_content='使用 FastAPI 开发接口。',
        confirmation_questions=['请确认数据库类型'],
        confirmed_answers=[{'question': '请确认数据库类型', 'answer': '数据库是 MySQL'}],
        feedback='数据库是 MySQL',
    )
    assert '问题，不是事实' in CONFIRMATION_SYSTEM_PROMPT
    assert '<confirmation_context>' in confirmation_prompt
    assert '数据库是 MySQL' in confirmation_prompt


@pytest.mark.asyncio
async def test_ai_confirmation_keeps_unresolved_question_when_content_is_unchanged(monkeypatch):
    import app.routers.resume_optimizations as routes

    class NoChangeGateway:
        async def generate_json(self, **kwargs):
            payload = {
                'optimized_content': '原简历内容',
                'optimization_summary': '信息不足，未修改',
                'score_improvement': 80,
                'change_items': [],
                'resolved_questions': ['请确认数据库类型'],
                'remaining_questions': [],
            }
            return TextGenerationResult(content=json.dumps(payload, ensure_ascii=False), usage={})

    monkeypatch.setattr(routes, 'TencentMaaSModelGateway', NoChangeGateway)
    result = await routes.apply_ai_confirmations(
        optimized_content='原简历内容',
        original_content='原简历内容',
        confirmation_questions=['请确认数据库类型'],
        score_improvement=80,
    )
    assert result['resolved_questions'] == []
    assert result['remaining_questions'] == ['请确认数据库类型']


@pytest.mark.asyncio
async def test_ai_confirmation_blocks_unconfirmed_number_without_raising(monkeypatch):
    import app.routers.resume_optimizations as routes

    class UnsupportedNumberGateway:
        async def generate_json(self, **kwargs):
            payload = {
                'optimized_content': '原简历内容，性能提升50%',
                'optimization_summary': '补充量化结果',
                'score_improvement': 90,
                'change_items': [{'section': '项目', 'original': '原简历内容', 'optimized': '性能提升50%'}],
                'resolved_questions': ['请确认是否有量化结果'],
                'remaining_questions': [],
            }
            return TextGenerationResult(content=json.dumps(payload, ensure_ascii=False), usage={})

    monkeypatch.setattr(routes, 'TencentMaaSModelGateway', UnsupportedNumberGateway)
    result = await routes.apply_ai_confirmations(
        optimized_content='原简历内容',
        original_content='原简历内容',
        confirmation_questions=['请确认是否有量化结果'],
        score_improvement=80,
    )
    assert result['optimized_content'] == '原简历内容'
    assert result['change_items'] == []
    assert result['remaining_questions'] == ['请确认是否有量化结果']


@pytest.mark.asyncio
async def test_ai_confirmation_uses_confirmed_answer_and_returns_actual_saved_text(monkeypatch):
    import app.routers.resume_optimizations as routes

    class ConfirmedAnswerGateway:
        async def generate_json(self, **kwargs):
            payload = {
                'optimized_content': '项目经历\n接口性能提升50%',
                'optimization_summary': '已整合用户确认的量化成果',
                'score_improvement': 85,
                'change_items': [{
                    'section': '项目经历',
                    'original': '项目经历',
                    'optimized': '接口性能提升50%',
                    'reason': '补充用户确认的成果',
                    'evidence': '用户确认性能提升50%',
                    'evidence_source': 'user_confirmation',
                    'requires_confirmation': False,
                }],
                'added_content': '模型返回的不准确摘要',
                'resolved_questions': ['请确认性能提升比例'],
                'remaining_questions': [],
            }
            return TextGenerationResult(content=json.dumps(payload, ensure_ascii=False), usage={})

    monkeypatch.setattr(routes, 'TencentMaaSModelGateway', ConfirmedAnswerGateway)
    result = await routes.apply_ai_confirmations(
        optimized_content='项目经历',
        original_content='项目经历',
        confirmation_questions=['请确认性能提升比例'],
        confirmed_answers=[ManualConfirmationItem(
            question='请确认性能提升比例',
            answer='接口性能提升50%',
        )],
        score_improvement=80,
    )
    assert result['optimized_content'] == '项目经历\n接口性能提升50%'
    assert result['added_content'] == '接口性能提升50%'
    assert result['resolved_questions'] == ['请确认性能提升比例']
    assert result['remaining_questions'] == []


def test_saved_resume_optimization_routes_are_registered():
    from app.main import app

    paths = app.openapi()['paths']
    assert '/api/resumes/{resume_id}/optimizations/{optimization_id}/confirmations/ai-preview' in paths
    assert '/api/resumes/{resume_id}/optimizations/{optimization_id}/confirmations/manual-preview' in paths
    assert '/api/resume-optimizations/saved' in paths
    assert '/api/resume-optimizations/saved/{saved_optimization_id}' in paths
    assert '/api/resume-optimizations/saved/{saved_optimization_id}/download' in paths
    assert 'post' in paths['/api/resumes/{resume_id}/optimizations/{optimization_id}/confirmations/ai-preview']
    assert 'post' in paths['/api/resumes/{resume_id}/optimizations/{optimization_id}/confirmations/manual-preview']
    assert 'get' in paths['/api/resume-optimizations/saved']
    assert 'get' in paths['/api/resume-optimizations/saved/{saved_optimization_id}']
    assert 'delete' in paths['/api/resume-optimizations/saved/{saved_optimization_id}']


class FakeGateway:
    async def generate_json(self, *, system_prompt: str, user_prompt: str, max_tokens: int | None = None):
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
    async def retrieve(self, query: str, *, top_k: int | None = None, filters=None):
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
