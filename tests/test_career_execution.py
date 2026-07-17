from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.schemas.career_plan import CareerTaskCheckinRequest
from app.services import career_execution_service as service
from app.services.career_plan_service import CareerPlanError


def build_plan(status="completed"):
    return SimpleNamespace(
        id=10,
        user_id=7,
        status=status,
        accepted_at=None,
        learning_path={
            "total_weeks": 4,
            "stages": [{
                "stage": "基础巩固",
                "duration": "第1-2周",
                "goals": ["掌握基础"],
                "topics": ["FastAPI"],
                "tasks": ["完成路由练习"],
                "practice_tasks": ["实现 REST API"],
                "deliverables": ["项目代码"],
            }],
        },
        action_plan={
            "this_week": ["整理学习计划"],
            "this_month": [],
            "portfolio_projects": [],
            "resume_actions": ["更新项目描述"],
            "review_points": ["复盘本周进度"],
        },
    )


def test_execution_tasks_are_deterministic_and_cover_plan_sections():
    execution = SimpleNamespace(id=20, user_id=7, career_plan_id=10, start_date=date(2026, 7, 16))
    first = service.build_execution_tasks(build_plan(), execution)
    second = service.build_execution_tasks(build_plan(), execution)

    assert first
    assert [task.task_key for task in first] == [task.task_key for task in second]
    assert len({task.task_key for task in first}) == len(first)
    assert {task.task_type for task in first} >= {
        "learning", "practice", "deliverable", "job_search", "review"
    }
    assert all(task.planned_date >= execution.start_date for task in first)


def test_streak_is_calculated_from_current_completed_tasks_only():
    today = date(2026, 7, 16)
    tasks = [
        SimpleNamespace(status="completed", checked_in_at=datetime(2026, 7, 14, 12)),
        SimpleNamespace(status="completed", checked_in_at=datetime(2026, 7, 15, 12)),
        SimpleNamespace(status="completed", checked_in_at=datetime(2026, 7, 16, 12)),
        SimpleNamespace(status="pending", checked_in_at=datetime(2026, 7, 13, 12)),
    ]
    assert service.calculate_streaks(tasks, today) == (3, 3)


class FakeDb:
    async def execute(self, statement):
        return None

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_accept_plan_is_idempotent_and_does_not_duplicate_tasks(monkeypatch):
    db = FakeDb()
    plan = build_plan()
    execution = None
    tasks = []
    pause_calls = 0

    async def get_plan(db, plan_id, user_id):
        return plan if (plan_id, user_id) == (10, 7) else None

    async def get_execution(db, plan_id, user_id):
        return execution

    async def pause(db, user_id):
        nonlocal pause_calls
        pause_calls += 1

    async def create_execution(db, item):
        nonlocal execution
        item.id = 20
        execution = item
        return item

    async def get_tasks(db, execution_id, user_id):
        return tasks

    async def create_tasks(db, items):
        tasks.extend(items)
        return items

    monkeypatch.setattr(service, "get_plan", get_plan)
    monkeypatch.setattr(service, "get_execution_by_plan", get_execution)
    monkeypatch.setattr(service, "pause_active_executions", pause)
    monkeypatch.setattr(service, "create_execution", create_execution)
    monkeypatch.setattr(service, "get_execution_tasks", get_tasks)
    monkeypatch.setattr(service, "create_execution_tasks", create_tasks)

    first_plan, first_execution = await service.accept_career_plan(db, user_id=7, plan_id=10)
    task_count = len(tasks)
    second_plan, second_execution = await service.accept_career_plan(db, user_id=7, plan_id=10)

    assert first_plan.status == second_plan.status == "accepted"
    assert first_execution.id == second_execution.id == 20
    assert len(tasks) == task_count > 0
    assert pause_calls == 1


@pytest.mark.asyncio
async def test_checkin_same_status_is_idempotent(monkeypatch):
    db = FakeDb()
    task = SimpleNamespace(
        id=30,
        user_id=7,
        execution_plan_id=20,
        status="pending",
        checkin_note=None,
        checked_in_at=None,
    )
    execution = SimpleNamespace(id=20, status="active")
    checkins = []

    async def get_task(db, task_id, user_id):
        return task if (task_id, user_id) == (30, 7) else None

    async def get_execution(db, execution_id, user_id):
        return execution

    async def create_checkin(db, item):
        checkins.append(item)
        return item

    async def overview(db, execution, user_id):
        return {"status": task.status}

    monkeypatch.setattr(service, "get_owned_execution_task", get_task)
    monkeypatch.setattr(service, "get_execution_by_id", get_execution)
    monkeypatch.setattr(service, "create_checkin", create_checkin)
    monkeypatch.setattr(service, "build_execution_overview", overview)

    request = CareerTaskCheckinRequest(status="completed", note="完成练习")
    await service.check_in_execution_task(db, user_id=7, task_id=30, request=request)
    await service.check_in_execution_task(db, user_id=7, task_id=30, request=request)

    assert task.status == "completed"
    assert task.checkin_note == "完成练习"
    assert len(checkins) == 1


@pytest.mark.asyncio
async def test_checkin_hides_other_users_task_as_404(monkeypatch):
    async def get_task(db, task_id, user_id):
        return None

    monkeypatch.setattr(service, "get_owned_execution_task", get_task)
    with pytest.raises(CareerPlanError) as exc_info:
        await service.check_in_execution_task(
            FakeDb(),
            user_id=8,
            task_id=30,
            request=CareerTaskCheckinRequest(status="completed"),
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_complete_all_has_no_week_stage_or_daily_limit(monkeypatch):
    db = FakeDb()
    execution = SimpleNamespace(id=20, status="active")
    tasks = [
        SimpleNamespace(
            id=1, status="pending", checked_in_at=None, is_active=False,
            checkin_note=None,
        ),
        SimpleNamespace(
            id=2, status="skipped", checked_in_at=None, is_active=False,
            checkin_note="稍后学习",
        ),
        SimpleNamespace(
            id=3, status="completed", checked_in_at=datetime(2026, 7, 16, 12),
            is_active=True, checkin_note="已完成",
        ),
    ]
    checkins = []

    async def get_execution(db, execution_id, user_id):
        return execution if (execution_id, user_id) == (20, 7) else None

    async def get_tasks(db, execution_id, user_id):
        return tasks

    async def create_checkin(db, item):
        checkins.append(item)
        return item

    async def overview(db, execution, user_id):
        return {"completed_tasks": sum(task.status == "completed" for task in tasks)}

    monkeypatch.setattr(service, "get_execution_by_id", get_execution)
    monkeypatch.setattr(service, "get_execution_tasks", get_tasks)
    monkeypatch.setattr(service, "create_checkin", create_checkin)
    monkeypatch.setattr(service, "build_execution_overview", overview)

    result = await service.complete_all_execution_tasks(
        db, user_id=7, execution_plan_id=20
    )

    assert result["completed_count"] == 2
    assert result["overview"]["completed_tasks"] == 3
    assert all(task.status == "completed" for task in tasks)
    assert all(task.is_active for task in tasks)
    assert len(checkins) == 2
