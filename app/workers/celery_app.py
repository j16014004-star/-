"""Durable Redis/Celery entry point for browser and AI workers."""
from __future__ import annotations

import asyncio
from typing import Awaitable

from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "ai_career_agent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    task_time_limit=max(60, settings.WORKER_TASK_TIMEOUT_SECONDS),
    task_soft_time_limit=max(30, settings.WORKER_TASK_TIMEOUT_SECONDS - 30),
    result_expires=86400,
)


@celery_app.task(name="app.workers.health")
def worker_health() -> dict:
    return {"status": "ok"}


def _runner(module: str, identifier: str) -> Awaitable:
    if module == "app.workers.platform_login_worker":
        from app.workers.platform_login_worker import run_login
        return run_login(identifier)
    if module == "app.workers.recommendation_worker":
        from app.workers.recommendation_worker import run_worker
        return run_worker(identifier)
    if module == "app.workers.ai_task_worker":
        from app.workers.ai_task_worker import run
        return run(identifier)
    if module == "app.workers.hr_action_worker":
        from app.workers.hr_action_worker import run
        return run(int(identifier))
    if module == "app.workers.hr_monitor_worker":
        from app.workers.hr_monitor_worker import run
        return run(int(identifier))
    raise ValueError(f"不支持的 worker 模块: {module}")


@celery_app.task(
    bind=True,
    name="app.workers.execute",
    autoretry_for=(OSError, ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=max(0, settings.WORKER_TASK_MAX_RETRIES),
)
def execute_worker(self, module: str, identifier: str) -> int:
    from app.workers.ai_task_worker import configure_event_loop

    configure_event_loop()
    asyncio.run(_runner(module, identifier))
    return 0
