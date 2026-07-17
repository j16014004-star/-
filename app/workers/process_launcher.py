from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKER_LOG_DIR = PROJECT_ROOT / "logs" / "workers"


class WorkerLaunchError(RuntimeError):
    """Raised when a browser worker process cannot be started."""


def launch_login_worker(session_id: str) -> int | str:
    return _launch_worker("app.workers.platform_login_worker", session_id)


def launch_recommendation_worker(task_id: str) -> int | str:
    return _launch_worker("app.workers.recommendation_worker", task_id)


def launch_ai_task_worker(task_id: str) -> int | str:
    return _launch_worker('app.workers.ai_task_worker', task_id)


def launch_hr_action_worker(action_id: int) -> int | str:
    return _launch_worker('app.workers.hr_action_worker', str(action_id))


def launch_hr_monitor_worker(workspace_id: int) -> int | str:
    return _launch_worker('app.workers.hr_monitor_worker', str(workspace_id))


def _launch_worker(module: str, identifier: str) -> int | str:
    from app.core.config import settings

    if settings.WORKER_BACKEND.strip().lower() == "celery":
        try:
            from app.workers.celery_app import execute_worker

            result = execute_worker.apply_async(
                args=[module, identifier],
                time_limit=max(60, settings.WORKER_TASK_TIMEOUT_SECONDS),
                soft_time_limit=max(30, settings.WORKER_TASK_TIMEOUT_SECONDS - 30),
            )
            return result.id
        except Exception as exc:
            raise WorkerLaunchError(f"无法提交 Celery worker 任务: {exc}") from exc
    if settings.WORKER_BACKEND.strip().lower() != "subprocess":
        raise WorkerLaunchError("WORKER_BACKEND 仅支持 celery 或 subprocess")

    WORKER_LOG_DIR.mkdir(parents=True, exist_ok=True)
    safe_identifier = "".join(
        char if char.isalnum() or char in "-_" else "_" for char in identifier
    )
    log_path = WORKER_LOG_DIR / f"{module.rsplit('.', 1)[-1]}-{safe_identifier}.log"
    command = [sys.executable, "-m", module, identifier]
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")

    creationflags = 0
    if os.name == "nt":
        creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        creationflags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)

    try:
        with log_path.open("ab") as log_file:
            started_at = datetime.now(timezone.utc).isoformat()
            log_file.write(f"\n[{started_at}] starting {' '.join(command)}\n".encode("utf-8"))
            process = subprocess.Popen(
                command,
                cwd=str(PROJECT_ROOT),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                creationflags=creationflags,
            )
    except OSError as exc:
        raise WorkerLaunchError(f"无法启动 worker 进程: {exc}") from exc

    return process.pid
