'''Resume optimization endpoints.'''
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.crud.resume_optimization import get_owned_optimization_version
from app.models.user import User
from app.schemas.resume_optimization import ResumeOptimizationRequest
from app.services.resume_optimization_service import ResumeOptimizationError, start_resume_optimization


router = APIRouter(prefix='/api/resumes', tags=['简历AI优化'])


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
    change_items = version.change_items or []
    first_change = change_items[0] if change_items else {}
    return {
        'code': 200,
        'message': 'success',
        'data': {
            'id': version.id,
            'optimization_summary': version.optimization_summary,
            'original': first_change.get('original') or version.original_content,
            'optimized': first_change.get('optimized') or version.optimized_content,
            'optimized_content': version.optimized_content,
            'score_improvement': version.score_improvement,
            'change_items': change_items,
            'confirmation_questions': version.confirmation_questions or [],
            'created_at': version.created_at,
        },
    }

