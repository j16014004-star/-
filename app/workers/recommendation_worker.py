from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone

from sqlalchemy import select

import app.models  # noqa: F401 - load all ORM tables for FK resolution
from app.core.database import async_session, engine
from app.crud.job_recommendation import update_task
from app.models.job import JobRecommendTask
from app.services.recommendation_task_service import run_recommendation_task


TASK_WAIT_SECONDS = 10


def configure_event_loop() -> None:
    if sys.platform != "win32":
        return
    policy_factory = getattr(asyncio, "WindowsProactorEventLoopPolicy", None)
    if policy_factory is not None:
        asyncio.set_event_loop_policy(policy_factory())


async def wait_for_task(task_id: str) -> bool:
    deadline = asyncio.get_running_loop().time() + TASK_WAIT_SECONDS
    while True:
        async with async_session() as db:
            result = await db.execute(
                select(JobRecommendTask.id).where(JobRecommendTask.id == task_id)
            )
            if result.scalar_one_or_none() is not None:
                return True
        if asyncio.get_running_loop().time() >= deadline:
            return False
        await asyncio.sleep(0.5)


async def mark_task_failed(task_id: str, message: str) -> None:
    async with async_session() as db:
        await update_task(
            db,
            task_id,
            status="failed",
            progress=100,
            error_message=message,
            finished_at=datetime.now(timezone.utc),
        )
        await db.commit()


async def run_worker(task_id: str) -> None:
    try:
        if not await wait_for_task(task_id):
            return
        await run_recommendation_task(task_id)
    except Exception as exc:
        await mark_task_failed(task_id, f"推荐任务 worker 执行失败: {exc}")
    finally:
        await engine.dispose()


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python -m app.workers.recommendation_worker <task_id>")
        return 2
    configure_event_loop()
    asyncio.run(run_worker(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
