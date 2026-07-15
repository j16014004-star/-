'''Resume optimization endpoints.'''
import re
from datetime import datetime, timezone
from urllib.parse import quote
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.resume_optimization_agent import _numbers, _parse_json_object
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
            normalized = {
                'section': str(item.get('section') or '').strip(),
                'original': str(item.get('original') or '').strip(),
                'optimized': str(item.get('optimized') or '').strip(),
                'reason': str(item.get('reason') or '').strip(),
                'evidence': str(item.get('evidence') or '').strip(),
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
            'requires_confirmation': False,
        }
        for item in confirmations
    ]


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
    feedback: str | None = None,
) -> dict:
    feedback = (feedback or '').strip()
    prompt = '\n'.join(
        [
            '请把用户待确认的问题转化为谨慎、事实不夸大的中文简历补充内容，并合并进 optimized_content。',
            '只能依据 confirmation_questions 中明确的问题做保守补充；不能虚构公司、学历、数字成果、证书、时间、金额或百分比。',
            '先检查 original_content 和 optimized_content；只有其中已有明确事实依据，或 feedback 明确提供了真实答案时，才允许解决对应问题。',
            '没有正文变化的问题不得放入 resolved_questions，必须保留在 remaining_questions。',
            '如果用户提供 feedback，需要按 feedback 调整补全方式；如果 feedback 与事实约束冲突，以事实约束为准。',
            '如果问题无法确定，请保留在 confirmation_questions 中。',
            '只输出 JSON 对象，字段为 optimized_content、optimization_summary、score_improvement、confirmation_questions、change_items、added_content、resolved_questions、remaining_questions；score_improvement 是优化后简历百分制评分 0-100。',
            '<optimized_content>',
            optimized_content,
            '</optimized_content>',
            '<original_content>',
            original_content,
            '</original_content>',
            '<confirmation_questions>',
            '\n'.join(f'- {item}' for item in confirmation_questions),
            '</confirmation_questions>',
            '<feedback>',
            feedback,
            '</feedback>',
        ]
    )
    try:
        response = await TencentMaaSModelGateway().generate_json(
            system_prompt='你是中文简历确认信息补全助手，只能输出 JSON。',
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
    change_items = payload.get('change_items') if isinstance(payload.get('change_items'), list) else []
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
    allowed_numbers = set(_numbers('\n'.join([original_content, optimized_content, feedback])))
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
    if not added_content and optimized_result == (optimized_content or '').strip() and remaining_questions:
        added_content = build_pending_confirmation_summary(remaining_questions)
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
    if not effective_questions and not (body.feedback or '').strip():
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
    payload = await apply_ai_confirmations(
        optimized_content=body.optimized_content,
        confirmation_questions=effective_questions,
        score_improvement=version.score_improvement,
        original_content=version.original_content,
        feedback=body.feedback,
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
    added_content = '\n'.join(f'- {item.answer.strip()}' for item in body.confirmations if item.answer.strip())
    resolved_questions = [item.question for item in body.confirmations]
    feedback = '\n'.join(
        f'问题：{item.question.strip()}\n用户确认的真实答案：{item.answer.strip()}'
        for item in body.confirmations
    )
    manual_changes = build_manual_change_items(body.confirmations)
    integrated_content = append_manual_confirmations(body.optimized_content, body.confirmations)
    integrated_changes = manual_changes
    try:
        payload = await apply_ai_confirmations(
            optimized_content=body.optimized_content,
            confirmation_questions=resolved_questions,
            score_improvement=version.score_improvement,
            original_content=version.original_content,
            feedback=feedback,
        )
        if payload['optimized_content'].strip() != body.optimized_content.strip():
            integrated_content = payload['optimized_content']
            integrated_changes = merge_change_items(payload['change_items'], manual_changes)
    except HTTPException:
        # 用户已提供真实答案时，即使模型临时不可用也能生成可采用的确定性预览。
        pass
    data = serialize_confirmation_preview(
        optimized_content=integrated_content,
        added_content=added_content,
        summary='已整合用户手动补充的确认信息',
        resolved_questions=resolved_questions,
        remaining_questions=remove_confirmed_questions(
            version.confirmation_questions or [],
            resolved_questions,
        ),
        change_items=integrated_changes,
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
    if not effective_questions and not (body.feedback or '').strip():
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
    version.optimized_content = body.optimized_content
    version.confirmation_questions = (
        body.confirmation_questions
        if body.confirmation_questions is not None
        else version.confirmation_questions or []
    )
    if body.change_items is not None:
        version.change_items = merge_change_items(version.change_items, body.change_items)
    version.confirmation_actions = merge_confirmation_actions(
        version.confirmation_actions,
        [item.model_dump(mode='json') for item in body.confirmation_actions],
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
        raise HTTPException(status_code=404, detail='优化简历不存在或无权限访问')
    await db.delete(version)
    await db.commit()
    return {
        'code': 200,
        'message': 'success',
        'data': None,
    }
