'''Independent worker process for AI tasks.'''
from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

import app.models  # noqa: F401
from app.core.database import async_session, engine
from app.models.ai import AITask
from app.services.career_plan_service import execute_career_plan_task
from app.services.career_question_service import execute_career_question_task
from app.services.career_assessment_service import (
    execute_stage_assessment_evaluation_task,
    execute_stage_assessment_task,
)
from app.services.resume_optimization_service import execute_resume_optimization_task
from app.services.hr_service import execute_hr_application_draft_task


TASK_WAIT_SECONDS = 10


def configure_event_loop() -> None:
    if sys.platform != 'win32':
        return
    policy_factory = getattr(asyncio, 'WindowsProactorEventLoopPolicy', None)
    if policy_factory is not None:
        asyncio.set_event_loop_policy(policy_factory())


async def wait_for_task(task_id: str) -> AITask | None:
    deadline = asyncio.get_running_loop().time() + TASK_WAIT_SECONDS
    while asyncio.get_running_loop().time() < deadline:
        async with async_session() as db:
            result = await db.execute(select(AITask).where(AITask.id == task_id))
            task = result.scalar_one_or_none()
            if task is not None:
                return task
        await asyncio.sleep(0.2)
    return None


async def run(task_id: str) -> int:
    task = await wait_for_task(task_id)
    if task is None:
        print(f'[ai-worker] task not found after wait: {task_id}')
        return 2
    if task.task_type not in ('resume_optimization', 'career_plan', 'career_plan_question', 'career_stage_assessment', 'career_stage_assessment_evaluation', 'hr_application_draft'):
        print(f'[ai-worker] unsupported task type: {task.task_type}')
        return 3
    print(f'[ai-worker] start task={task_id} type={task.task_type}')
    try:
        if task.task_type == 'resume_optimization':
            await execute_resume_optimization_task(task_id)
        elif task.task_type == 'career_plan':
            await execute_career_plan_task(task_id)
        elif task.task_type == 'career_plan_question':
            await execute_career_question_task(task_id)
        elif task.task_type == 'career_stage_assessment':
            await execute_stage_assessment_task(task_id)
        elif task.task_type == 'career_stage_assessment_evaluation':
            await execute_stage_assessment_evaluation_task(task_id)
        elif task.task_type == 'hr_application_draft':
            await execute_hr_application_draft_task(task_id)
    finally:
        await engine.dispose()
    print(f'[ai-worker] finished task={task_id}')
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print('usage: python -m app.workers.ai_task_worker <task_id>')
        return 1
    configure_event_loop()
    return asyncio.run(run(sys.argv[1]))


if __name__ == '__main__':
    raise SystemExit(main())
