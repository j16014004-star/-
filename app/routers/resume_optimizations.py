'''Resume optimization endpoints.'''
import re
from datetime import datetime, timezone
from urllib.parse import quote
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.resume_optimization_agent import _numbers, _parse_json_object
from app.ai.resume_optimization_prompt import CONFIRMATION_SYSTEM_PROMPT, build_confirmation_prompt
from app.ai.tencent_maas import TencentMaaSError, TencentMaaSModelGateway
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.crud.resume import get_resume_by_id
from app.crud.resume_optimization import (
    get_owned_optimization_version,
    get_owned_saved_optimization_version,
    list_saved_optimization_versions,
)
from app.models.user import User
from app.schemas.resume_optimization import (
    ConfirmationAIApplyRequest,
    ConfirmationDismissRequest,
    ConfirmationManualApplyRequest,
    OptimizationSaveRequest,
    ResumeOptimizationRequest,
)
from app.services.resume_optimization_service import ResumeOptimizationError, start_resume_optimization


router = APIRouter(prefix='/api/resumes', tags=['简历AI优化'])
saved_router = APIRouter(prefix='/api/resume-optimizations', tags=['保存的优化简历'])


def serialize_optimization_version(version) -> dict:
    change_items = version.change_items or []
    return {
        'id': version.id,
        'resume_id': version.resume_id,
        'title': version.title,
        'is_saved': version.is_saved,
        'saved_at': version.saved_at,
        'optimization_summary': version.optimization_summary,
        'original_content': version.original_content,
        'original': version.original_content,
        'optimized': version.optimized_content,
        'optimized_content': version.optimized_content,
        'score_improvement': version.score_improvement,
        'change_items': change_items,
        'changes': change_items,
        'confirmation_questions': version.confirmation_questions or [],
        'confirmation_actions': version.confirmation_actions or [],
        'created_at': version.created_at,
    }


async def build_saved_title(db: AsyncSession, version, user_id: int) -> str:
    resume = await get_resume_by_id(db, version.resume_id, user_id)
    base_title = (resume.title if resume else None) or f'简历{version.resume_id}'
    suffix = '-优化简历'
    return base_title if base_title.endswith(suffix) else f'{base_title}{suffix}'


def remove_confirmed_questions(current: list[str], handled: list[str]) -> list[str]:
    handled_set = {item.strip() for item in handled if item.strip()}
    return [item for item in current if item.strip() not in handled_set]


def merge_change_items(*groups: list[dict] | None, limit: int = 50) -> list[dict]:
    merged: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for group in groups:
        for item in group or []:
            if not isinstance(item, dict):
                continue
            evidence_source = str(item.get('evidence_source') or 'original_resume').strip()
            if evidence_source not in {'original_resume', 'user_confirmation', 'knowledge_base'}:
                evidence_source = 'original_resume'
            normalized = {
                'section': str(item.get('section') or '').strip(),
                'original': str(item.get('original') or '').strip(),
                'optimized': str(item.get('optimized') or '').strip(),
                'reason': str(item.get('reason') or '').strip(),
                'evidence': str(item.get('evidence') or '').strip(),
                'evidence_source': evidence_source,
                'requires_confirmation': bool(item.get('requires_confirmation', False)),
            }
            if not normalized['section'] or not normalized['original'] or not normalized['optimized']:
                continue
            key = (normalized['section'], normalized['original'], normalized['optimized'])
            if key in seen:
                continue
            seen.add(key)
            merged.append(normalized)
            if len(merged) >= limit:
                return merged
    return merged


def merge_confirmation_actions(*groups: list[dict] | None, limit: int = 30) -> list[dict]:
    merged: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for group in groups:
        for item in group or []:
            if not isinstance(item, dict):
                continue
            key = (
                str(item.get('type') or ''),
                str(item.get('created_at') or ''),
                str(item.get('added_content') or ''),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
            if len(merged) >= limit:
                return merged
    return merged


def append_manual_confirmations(content: str, confirmations: list) -> str:
    lines = [content.rstrip(), '', '补充确认信息：']
    for item in confirmations:
        lines.append(f'- {item.answer.strip()}')
    return '\n'.join(lines).strip()


def build_manual_change_items(confirmations: list) -> list[dict]:
    return [
        {
            'section': '补充确认信息',
            'original': item.question,
            'optimized': item.answer,
            'reason': '用户手动确认后加入简历',
            'evidence': '来自用户在确认信息表单中填写的答案',
            'evidence_source': 'user_confirmation',
            'requires_confirmation': False,
        }
        for item in confirmations
    ]


def build_confirmed_answer_fallback(
    optimized_content: str,
    confirmed_answers: list,
    confirmation_questions: list[str],
    score_improvement: int | None,
) -> dict:
    resolved_questions = [item.question.strip() for item in confirmed_answers]
    return {
        'optimized_content': append_manual_confirmations(optimized_content, confirmed_answers),
        'optimization_summary': '已将用户确认的真实答案加入优化简历',
        'added_content': '\n'.join(f'- {item.answer.strip()}' for item in confirmed_answers),
        'score_improvement': safe_score(score_improvement, score_improvement),
        'confirmation_questions': remove_confirmed_questions(confirmation_questions, resolved_questions),
        'resolved_questions': resolved_questions,
        'remaining_questions': remove_confirmed_questions(confirmation_questions, resolved_questions),
        'change_items': build_manual_change_items(confirmed_answers),
    }


def serialize_confirmation_preview(
    *,
    optimized_content: str,
    added_content: str,
    summary: str,
    resolved_questions: list[str] | None = None,
    remaining_questions: list[str] | None = None,
    change_items: list | None = None,
    preview_id: str | None = None,
    has_changes: bool | None = None,
) -> dict:
    added_content = (added_content or '').strip()
    summary = (summary or '').strip()
    if not added_content:
        added_content = summary or 'AI 未直接新增简历事实内容，仍需用户补充或确认后再加入简历。'
    return {
        'preview_id': preview_id or str(uuid4()),
        'added_content': added_content,
        'optimized_content': optimized_content,
        'summary': summary,
        'resolved_questions': resolved_questions or [],
        'remaining_questions': remaining_questions or [],
        'change_items': change_items or [],
        'has_changes': bool(change_items) if has_changes is None else has_changes,
    }


def extract_added_content(before: str, after: str, fallback: str = '') -> str:
    before = (before or '').strip()
    after = (after or '').strip()
    if not after or after == before:
        return fallback.strip()
    if after.startswith(before):
        added = after[len(before):].strip()
        if added:
            return added
    before_lines = {line.strip() for line in before.splitlines() if line.strip()}
    added_lines = [line.strip() for line in after.splitlines() if line.strip() and line.strip() not in before_lines]
    if added_lines:
        return '\n'.join(added_lines[:12])
    return fallback.strip() or 'AI 已根据待确认信息调整优化后的简历内容，请预览确认。'


def derive_actual_added_content(
    before: str,
    after: str,
    change_items: list[dict] | None,
    *,
    evidence_source: str | None = None,
) -> str:
    before = (before or '').strip()
    after = (after or '').strip()
    snippets: list[str] = []
    for item in change_items or []:
        if evidence_source and item.get('evidence_source') != evidence_source:
            continue
        optimized = str(item.get('optimized') or '').strip()
        if not optimized or optimized in before or optimized not in after or optimized in snippets:
            continue
        snippets.append(optimized)
    if snippets:
        return '\n\n'.join(snippets[:12])
    return extract_added_content(before, after)


def missing_confirmation_content(
    final_content: str,
    change_items: list[dict] | None,
    confirmation_actions: list[dict] | None = None,
) -> list[str]:
    final_content = (final_content or '').strip()
    missing: list[str] = []
    for item in change_items or []:
        if item.get('evidence_source') != 'user_confirmation':
            continue
        optimized = str(item.get('optimized') or '').strip()
        if optimized and optimized not in final_content:
            missing.append(optimized)
    for action in confirmation_actions or []:
        if action.get('type') not in {'ai', 'manual'}:
            continue
        added_content = str(action.get('added_content') or '').strip()
        if not added_content:
            continue
        snippets = [part.strip() for part in re.split(r'\n\s*\n', added_content) if part.strip()]
        for snippet in snippets:
            if snippet not in final_content:
                missing.append(snippet)
    return list(dict.fromkeys(missing))


def build_pending_confirmation_summary(questions: list[str]) -> str:
    valid_questions = [question.strip() for question in questions if question.strip()]
    if not valid_questions:
        return 'AI 未直接新增简历事实内容，当前没有可补充的待确认问题。'
    lines = [
        'AI 未直接新增简历事实内容，因为以下信息需要用户确认后才能写入简历：',
    ]
    lines.extend(f'- {question}' for question in valid_questions[:8])
    if len(valid_questions) > 8:
        lines.append(f'- 其余 {len(valid_questions) - 8} 条待确认信息请继续补充确认。')
    return '\n'.join(lines)


def split_redundant_date_questions(questions: list[str], original_content: str) -> tuple[list[str], list[str]]:
    source_numbers = set(_numbers(original_content))
    kept: list[str] = []
    skipped: list[str] = []
    for question in questions:
        question_numbers = set(_numbers(question))
        date_numbers = {number for number in question_numbers if re_full_date_number(number)}
        if date_numbers and date_numbers.issubset(source_numbers):
            skipped.append(question)
        else:
            kept.append(question)
    return kept, skipped


def re_full_date_number(value: str) -> bool:
    return bool(re.fullmatch(r'(?:19|20)\d{2}\.(?:0[1-9]|1[0-2])', value))


def safe_score(value, fallback: int | None) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        score = int(fallback or 0)
    return max(0, min(100, score))


async def apply_ai_confirmations(
    *,
    optimized_content: str,
    confirmation_questions: list[str],
    score_improvement: int | None,
    original_content: str = '',
    confirmed_answers: list | None = None,
    feedback: str | None = None,
) -> dict:
    feedback = (feedback or '').strip()
    confirmed_answer_data: list[dict[str, str]] = []
    for item in confirmed_answers or []:
        if isinstance(item, dict):
            question = item.get('question', '')
            answer = item.get('answer', '')
        else:
            question = getattr(item, 'question', '')
            answer = getattr(item, 'answer', '')
        confirmed_answer_data.append({
            'question': str(question).strip(),
            'answer': str(answer).strip(),
        })
    prompt = build_confirmation_prompt(
        optimized_content=optimized_content,
        original_content=original_content,
        confirmation_questions=confirmation_questions,
        confirmed_answers=confirmed_answer_data,
        feedback=feedback,
    )
    try:
        response = await TencentMaaSModelGateway().generate_json(
            system_prompt=CONFIRMATION_SYSTEM_PROMPT,
            user_prompt=prompt,
        )
    except TencentMaaSError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    try:
        payload = _parse_json_object(response.content)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    optimized_result = str(payload.get('optimized_content') or optimized_content).strip()
    summary = str(payload.get('optimization_summary') or '已根据待确认问题补充简历内容').strip()
    added_content = str(payload.get('added_content') or '').strip()
    raw_change_items = payload.get('change_items') if isinstance(payload.get('change_items'), list) else []
    change_items = merge_change_items(raw_change_items)
    remaining_questions = [
        str(item).strip()
        for item in (payload.get('remaining_questions') or payload.get('confirmation_questions') or [])
        if str(item).strip()
    ]
    resolved_questions = [
        str(item).strip()
        for item in (payload.get('resolved_questions') or [])
        if str(item).strip()
    ]
    confirmed_answer_text = '\n'.join(item['answer'] for item in confirmed_answer_data)
    allowed_numbers = set(_numbers('\n'.join([original_content, optimized_content, confirmed_answer_text])))
    unsupported_numbers = set(_numbers(optimized_result)) - allowed_numbers
    if unsupported_numbers:
        optimized_result = optimized_content.strip()
        change_items = []
        resolved_questions = []
        remaining_questions = list(dict.fromkeys(confirmation_questions + remaining_questions))
        summary = 'AI 生成内容包含未获用户确认的数字，已保留原简历并继续等待确认。'
        added_content = build_pending_confirmation_summary(remaining_questions)
    elif optimized_result == optimized_content.strip():
        change_items = []
        resolved_questions = []
        remaining_questions = list(dict.fromkeys(confirmation_questions + remaining_questions))
    question_set = set(confirmation_questions)
    resolved_questions = list(dict.fromkeys(
        question for question in resolved_questions if question in question_set
    ))
    resolved_set = set(resolved_questions)
    remaining_questions = list(dict.fromkeys(
        question for question in remaining_questions
        if question in question_set and question not in resolved_set
    ))
    classified = resolved_set | set(remaining_questions)
    remaining_questions.extend(
        question for question in confirmation_questions if question not in classified
    )
    if not added_content and optimized_result == (optimized_content or '').strip() and remaining_questions:
        added_content = build_pending_confirmation_summary(remaining_questions)
    elif optimized_result != (optimized_content or '').strip():
        added_content = derive_actual_added_content(
            optimized_content,
            optimized_result,
            change_items,
            evidence_source='user_confirmation' if confirmed_answer_data else None,
        )
    confirmation_questions_result = remaining_questions or [
        str(item).strip()
        for item in (payload.get('confirmation_questions') or [])
        if str(item).strip()
    ]
    return {
        'optimized_content': optimized_result,
        'optimization_summary': summary,
        'added_content': added_content or extract_added_content(optimized_content, optimized_result, summary),
        'score_improvement': safe_score(payload.get('score_improvement'), score_improvement),
        'confirmation_questions': confirmation_questions_result,
        'resolved_questions': resolved_questions,
        'remaining_questions': remaining_questions,
        'change_items': change_items,
    }


@router.post('/{resume_id}/optimizations')
async def create_resume_optimization(
    resume_id: int,
    body: ResumeOptimizationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await start_resume_optimization(
            db,
            user_id=current_user.id,
            resume_id=resume_id,
            request=body,
        )
    except ResumeOptimizationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    message = '简历优化任务已创建' if result.created else '已返回相同配置的简历优化任务'
    return {
        'code': 200,
        'message': message,
        'data': {
            'task_id': result.task.id,
            'status': result.task.status,
            'result_id': result.task.result_id,
            'poll_after_seconds': 2,
        },
    }


@router.get('/{resume_id}/optimizations/{optimization_id}')
async def get_resume_optimization(
    resume_id: int,
    optimization_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    version = await get_owned_optimization_version(
        db,
        optimization_id=optimization_id,
        resume_id=resume_id,
        user_id=current_user.id,
    )
    if version is None:
        raise HTTPException(status_code=404, detail='简历优化版本不存在')
    return {
        'code': 200,
        'message': 'success',
        'data': serialize_optimization_version(version),
    }


@router.post('/{resume_id}/optimizations/{optimization_id}/confirmations/ai-preview')
async def preview_confirmations_with_ai(
    resume_id: int,
    optimization_id: int,
    body: ConfirmationAIApplyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    version = await get_owned_optimization_version(
        db,
        optimization_id=optimization_id,
        resume_id=resume_id,
        user_id=current_user.id,
    )
    if version is None:
        raise HTTPException(status_code=404, detail='优化记录不存在或无权限访问')
    effective_questions, skipped_questions = split_redundant_date_questions(
        body.confirmation_questions,
        version.original_content,
    )
    effective_question_set = set(effective_questions)
    effective_answers = [
        item for item in body.confirmed_answers if item.question in effective_question_set
    ]
    if not effective_questions and not (body.feedback or '').strip() and not effective_answers:
        data = serialize_confirmation_preview(
            optimized_content=body.optimized_content,
            added_content='',
            summary='待确认问题均为原简历已有日期的格式变化，无需 AI 补全。',
            resolved_questions=body.confirmation_questions,
            remaining_questions=[],
            change_items=[],
            has_changes=False,
        )
        return {
            'code': 0,
            'message': 'success',
            'data': data,
        }
    try:
        payload = await apply_ai_confirmations(
            optimized_content=body.optimized_content,
            confirmation_questions=effective_questions,
            score_improvement=version.score_improvement,
            original_content=version.original_content,
            confirmed_answers=effective_answers,
            feedback=body.feedback,
        )
    except HTTPException:
        if not effective_answers:
            raise
        payload = build_confirmed_answer_fallback(
            body.optimized_content,
            effective_answers,
            effective_questions,
            version.score_improvement,
        )
    answered_questions = {item.question for item in effective_answers}
    confirmed_changes = [
        item for item in payload['change_items']
        if item.get('evidence_source') == 'user_confirmation'
        and str(item.get('optimized') or '').strip() in payload['optimized_content']
    ]
    if effective_answers and (
        payload['optimized_content'].strip() == body.optimized_content.strip()
        or not answered_questions.issubset(set(payload['resolved_questions']))
        or not confirmed_changes
    ):
        payload = build_confirmed_answer_fallback(
            body.optimized_content,
            effective_answers,
            effective_questions,
            version.score_improvement,
        )
    data = serialize_confirmation_preview(
        optimized_content=payload['optimized_content'],
        added_content=payload['added_content'],
        summary=payload['optimization_summary'],
        resolved_questions=list(dict.fromkeys(skipped_questions + payload['resolved_questions'])),
        remaining_questions=payload['remaining_questions'],
        change_items=payload['change_items'],
        has_changes=payload['optimized_content'].strip() != body.optimized_content.strip(),
    )
    return {
        'code': 0,
        'message': 'success',
        'data': data,
    }


@router.post('/{resume_id}/optimizations/{optimization_id}/confirmations/manual-preview')
async def preview_manual_confirmations(
    resume_id: int,
    optimization_id: int,
    body: ConfirmationManualApplyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    version = await get_owned_optimization_version(
        db,
        optimization_id=optimization_id,
        resume_id=resume_id,
        user_id=current_user.id,
    )
    if version is None:
        raise HTTPException(status_code=404, detail='优化记录不存在或无权限访问')
    resolved_questions = [item.question for item in body.confirmations]
    payload = build_confirmed_answer_fallback(
        body.optimized_content,
        body.confirmations,
        resolved_questions,
        version.score_improvement,
    )
    try:
        candidate = await apply_ai_confirmations(
            optimized_content=body.optimized_content,
            confirmation_questions=resolved_questions,
            score_improvement=version.score_improvement,
            original_content=version.original_content,
            confirmed_answers=body.confirmations,
            feedback=None,
        )
        confirmed_changes = [
            item for item in candidate['change_items']
            if item.get('evidence_source') == 'user_confirmation'
            and str(item.get('optimized') or '').strip() in candidate['optimized_content']
        ]
        if (
            candidate['optimized_content'].strip() != body.optimized_content.strip()
            and set(resolved_questions).issubset(set(candidate['resolved_questions']))
            and confirmed_changes
        ):
            payload = candidate
    except HTTPException:
        # 用户已提供真实答案时，即使模型临时不可用也能生成可采用的确定性预览。
        pass
    data = serialize_confirmation_preview(
        optimized_content=payload['optimized_content'],
        added_content=payload['added_content'],
        summary=payload['optimization_summary'],
        resolved_questions=resolved_questions,
        remaining_questions=remove_confirmed_questions(
            version.confirmation_questions or [],
            resolved_questions,
        ),
        change_items=payload['change_items'],
        has_changes=True,
    )
    return {
        'code': 0,
        'message': 'success',
        'data': data,
    }


@router.post('/{resume_id}/optimizations/{optimization_id}/confirmations/ai-apply')
async def apply_confirmations_with_ai(
    resume_id: int,
    optimization_id: int,
    body: ConfirmationAIApplyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    version = await get_owned_optimization_version(
        db,
        optimization_id=optimization_id,
        resume_id=resume_id,
        user_id=current_user.id,
    )
    if version is None:
        raise HTTPException(status_code=404, detail='优化记录不存在或无权限访问')
    effective_questions, skipped_questions = split_redundant_date_questions(
        body.confirmation_questions,
        version.original_content,
    )
    effective_question_set = set(effective_questions)
    effective_answers = [
        item for item in body.confirmed_answers if item.question in effective_question_set
    ]
    if not effective_questions and not (body.feedback or '').strip() and not effective_answers:
        version.confirmation_questions = remove_confirmed_questions(
            version.confirmation_questions or [],
            skipped_questions or body.confirmation_questions,
        )
        version.optimization_summary = '已忽略原简历已有日期的格式变化确认项'
        await db.commit()
        await db.refresh(version)
        return {
            'code': 0,
            'message': 'success',
            'data': serialize_optimization_version(version),
        }
    payload = await apply_ai_confirmations(
        optimized_content=body.optimized_content,
        confirmation_questions=effective_questions,
        score_improvement=version.score_improvement,
        original_content=version.original_content,
        confirmed_answers=effective_answers,
        feedback=body.feedback,
    )
    version.optimized_content = payload['optimized_content']
    version.optimization_summary = payload['optimization_summary']
    version.score_improvement = payload['score_improvement']
    version.confirmation_questions = remove_confirmed_questions(
        payload['confirmation_questions'],
        skipped_questions,
    )
    if payload['change_items']:
        version.change_items = merge_change_items(version.change_items, payload['change_items'])
    await db.commit()
    await db.refresh(version)
    return {
        'code': 0,
        'message': 'success',
        'data': serialize_optimization_version(version),
    }


@router.post('/{resume_id}/optimizations/{optimization_id}/confirmations/manual-apply')
async def apply_manual_confirmations(
    resume_id: int,
    optimization_id: int,
    body: ConfirmationManualApplyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    version = await get_owned_optimization_version(
        db,
        optimization_id=optimization_id,
        resume_id=resume_id,
        user_id=current_user.id,
    )
    if version is None:
        raise HTTPException(status_code=404, detail='优化记录不存在或无权限访问')
    version.optimized_content = append_manual_confirmations(body.optimized_content, body.confirmations)
    version.optimization_summary = '已加入用户手动补充的信息'
    version.confirmation_questions = remove_confirmed_questions(
        version.confirmation_questions or [],
        [item.question for item in body.confirmations],
    )
    version.score_improvement = min(100, (version.score_improvement or 0) + 3)
    version.change_items = (version.change_items or []) + build_manual_change_items(body.confirmations)
    await db.commit()
    await db.refresh(version)
    return {
        'code': 0,
        'message': 'success',
        'data': serialize_optimization_version(version),
    }


@router.post('/{resume_id}/optimizations/{optimization_id}/confirmations/dismiss')
async def dismiss_confirmations(
    resume_id: int,
    optimization_id: int,
    body: ConfirmationDismissRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    version = await get_owned_optimization_version(
        db,
        optimization_id=optimization_id,
        resume_id=resume_id,
        user_id=current_user.id,
    )
    if version is None:
        raise HTTPException(status_code=404, detail='优化记录不存在或无权限访问')
    if body.confirmation_questions:
        version.confirmation_questions = remove_confirmed_questions(
            version.confirmation_questions or [],
            body.confirmation_questions,
        )
    else:
        version.confirmation_questions = []
    version.optimization_summary = '已忽略待确认信息'
    await db.commit()
    await db.refresh(version)
    return {
        'code': 0,
        'message': 'success',
        'data': serialize_optimization_version(version),
    }


@router.post('/{resume_id}/optimizations/{optimization_id}/save')
async def save_optimization_content(
    resume_id: int,
    optimization_id: int,
    body: OptimizationSaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    version = await get_owned_optimization_version(
        db,
        optimization_id=optimization_id,
        resume_id=resume_id,
        user_id=current_user.id,
    )
    if version is None:
        raise HTTPException(status_code=404, detail='优化记录不存在或无权限访问')
    merged_change_items = (
        merge_change_items(version.change_items, body.change_items)
        if body.change_items is not None
        else version.change_items or []
    )
    incoming_actions = [item.model_dump(mode='json') for item in body.confirmation_actions]
    missing_content = missing_confirmation_content(
        body.optimized_content,
        merged_change_items,
        incoming_actions,
    )
    if missing_content:
        raise HTTPException(
            status_code=422,
            detail='最终简历缺少已采用的确认补充内容，请重新采用补全预览后再保存',
        )
    version.optimized_content = body.optimized_content
    version.confirmation_questions = (
        body.confirmation_questions
        if body.confirmation_questions is not None
        else version.confirmation_questions or []
    )
    if body.change_items is not None:
        version.change_items = merged_change_items
    version.confirmation_actions = merge_confirmation_actions(
        version.confirmation_actions,
        incoming_actions,
    )
    version.is_saved = True
    version.saved_at = datetime.now(timezone.utc).replace(tzinfo=None)
    version.title = version.title or await build_saved_title(db, version, current_user.id)
    await db.commit()
    await db.refresh(version)
    return {
        'code': 0,
        'message': 'success',
        'data': serialize_optimization_version(version),
    }


@saved_router.get('/saved')
async def list_saved_resume_optimizations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await list_saved_optimization_versions(
        db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return {
        'code': 200,
        'message': 'success',
        'data': {
            'items': [serialize_optimization_version(item) for item in items],
            'total': total,
            'page': page,
            'page_size': page_size,
        },
    }


@saved_router.get('/saved/{saved_optimization_id}')
async def get_saved_resume_optimization(
    saved_optimization_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    version = await get_owned_saved_optimization_version(
        db,
        optimization_id=saved_optimization_id,
        user_id=current_user.id,
    )
    if version is None:
        raise HTTPException(status_code=404, detail='优化简历不存在或无权限访问')
    return {
        'code': 200,
        'message': 'success',
        'data': serialize_optimization_version(version),
    }


@saved_router.get('/saved/{saved_optimization_id}/download')
async def download_saved_resume_optimization(
    saved_optimization_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    version = await get_owned_saved_optimization_version(
        db,
        optimization_id=saved_optimization_id,
        user_id=current_user.id,
    )
    if version is None:
        raise HTTPException(status_code=404, detail='优化简历不存在或无权限访问')
    filename = f'{version.title or f"优化简历-{version.id}"}.txt'
    disposition = f"attachment; filename*=UTF-8''{quote(filename)}"
    return Response(
        content=version.optimized_content,
        media_type='text/plain; charset=utf-8',
        headers={'Content-Disposition': disposition},
    )


@saved_router.delete('/saved/{saved_optimization_id}')
async def delete_saved_resume_optimization(
    saved_optimization_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    version = await get_owned_saved_optimization_version(
        db,
        optimization_id=saved_optimization_id,
        user_id=current_user.id,
    )
    if version is None:
        # DELETE 保持幂等：页面缓存、重复点击或原始简历级联删除后，
        # 客户端仍应当能够安全地完成本地清理与页面跳转。
        return {
            'code': 200,
            'message': '优化简历已删除或不存在',
            'data': None,
        }
    await db.delete(version)
    await db.commit()
    return {
        'code': 200,
        'message': 'success',
        'data': None,
    }
