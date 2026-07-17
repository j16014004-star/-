import sys
from types import ModuleType
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.workers import process_launcher


def test_celery_worker_backend_submits_durable_task(monkeypatch):
    captured = {}

    def fake_apply_async(*, args, time_limit, soft_time_limit):
        captured.update(
            args=args,
            time_limit=time_limit,
            soft_time_limit=soft_time_limit,
        )
        return SimpleNamespace(id="celery-task-1")

    monkeypatch.setattr(settings, "WORKER_BACKEND", "celery")
    monkeypatch.setattr(settings, "WORKER_TASK_TIMEOUT_SECONDS", 900)
    fake_task = SimpleNamespace(apply_async=fake_apply_async)
    fake_module = ModuleType("app.workers.celery_app")
    fake_module.execute_worker = fake_task
    monkeypatch.setitem(sys.modules, "app.workers.celery_app", fake_module)

    task_id = process_launcher.launch_hr_action_worker(42)

    assert task_id == "celery-task-1"
    assert captured["args"] == ["app.workers.hr_action_worker", "42"]
    assert captured["time_limit"] == 900
    assert captured["soft_time_limit"] == 870


def test_unknown_worker_backend_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "WORKER_BACKEND", "unknown")
    with pytest.raises(process_launcher.WorkerLaunchError):
        process_launcher.launch_hr_action_worker(42)
