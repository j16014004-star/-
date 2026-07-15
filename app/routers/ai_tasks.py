'''AI task status endpoint.'''
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.crud.ai_task import get_owned_ai_task
from app.models.user import User


router = APIRouter(prefix='/api/ai/tasks', tags=['AI任务'])


@router.get('/{task_id}')
async def get_ai_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await get_owned_ai_task(db, task_id, current_user.id)
    if task is None:
        raise HTTPException(status_code=404, detail='AI任务不存在')
    return {
        'code': 200,
        'message': 'success',
        'data': {
            'task_id': task.id,
            'task_type': task.task_type,
            'status': task.status,
            'progress': task.progress,
            'result_id': task.result_id,
            'error_message': task.error_message,
            'poll_after_seconds': 2,
        },
    }

