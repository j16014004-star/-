from contextlib import asynccontextmanager
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.routers import career_plans as career_router
from app.services import career_plan_service as service
from app.schemas.career_plan import CareerPlanCreateRequest


NOW = datetime(2026, 7, 16, 12, 0, 0)


def build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(career_router.profile_router)
    app.include_router(career_router.plan_router)

    async def fake_db():
        yield SimpleNamespace()

    async def fake_user():
        return SimpleNamespace(id=7)

    app.dependency_overrides[get_db] = fake_db
    app.dependency_overrides[get_current_user] = fake_user
    return app


def test_career_profile_file_plan_and_result_http_contracts(monkeypatch):
    profile = SimpleNamespace(
        id=11,
        user_id=7,
        education="本科",
        experience="1-3年",
        skills=["Python", "FastAPI"],
        work_description="负责后端接口开发",
        weekly_learning_hours=8,
        preferred_target_role="Python后端工程师",
        projects=[],
        created_at=NOW,
        updated_at=NOW,
    )
    attachment = SimpleNamespace(
        id=21,
        original_filename="project.txt",
        file_type="txt",
        file_size=7,
        status="completed",
        error_message=None,
    )
    task = SimpleNamespace(id="career-task-1", status="pending", result_id=None)
    plan = SimpleNamespace(
        id=31,
        user_id=7,
        profile_id=11,
        career_profile_summary={"summary": "适合继续发展 Python 后端"},
        recommended_roles=[],
        career_goals={"short_term": [], "medium_term": [], "long_term": []},
        skill_gap_analysis=[],
        learning_path={"total_weeks": 12, "hours_per_week": 8, "stages": []},
        action_plan={},
        risks_and_alternatives={},
        retrieval_source="qdrant_vector",
        retrieval_error=None,
        retrieved_chunk_ids=["chunk-1"],
        knowledge_base_version="v1",
        created_at=NOW,
    )

    async def create_profile(*args, **kwargs):
        assert kwargs["user_id"] == 7
        return profile

    async def upload(*args, **kwargs):
        assert kwargs["user_id"] == 7
        return attachment

    async def remove(*args, **kwargs):
        assert kwargs == {"user_id": 7, "file_id": 21}

    async def start(*args, **kwargs):
        assert kwargs["request"].profile_id == 11
        return SimpleNamespace(task=task, plan=plan)

    async def get_owned_plan(*args, **kwargs):
        plan_id, user_id = args[1], args[2]
        return plan if (plan_id, user_id) == (31, 7) else None

    monkeypatch.setattr(career_router, "create_career_profile", create_profile)
    monkeypatch.setattr(career_router, "upload_project_attachment", upload)
    monkeypatch.setattr(career_router, "remove_project_attachment", remove)
    monkeypatch.setattr(career_router, "start_career_plan", start)
    monkeypatch.setattr(career_router, "get_plan", get_owned_plan)

    with TestClient(build_test_app()) as client:
        profile_response = client.post(
            "/api/career-planning/profiles",
            json={
                "education": "本科",
                "experience": "1-3年",
                "skills": ["Python", "FastAPI"],
                "work_description": "负责后端接口开发",
                "weekly_learning_hours": 8,
                "preferred_target_role": "Python后端工程师",
                "projects": [],
            },
        )
        assert profile_response.status_code == 200
        assert profile_response.json()["data"]["id"] == 11

        upload_response = client.post(
            "/api/career-plans/project-files/upload",
            files={"file": ("project.txt", b"project", "text/plain")},
        )
        assert upload_response.status_code == 200
        assert upload_response.json()["data"]["id"] == 21
        assert client.delete("/api/career-plans/project-files/21").status_code == 200

        start_response = client.post("/api/career-plans", json={"profile_id": 11})
        assert start_response.status_code == 200
        assert start_response.json()["data"] == {
            "task_id": "career-task-1",
            "status": "pending",
            "result_id": None,
            "plan_id": 31,
            "poll_after_seconds": 2,
        }

        result_response = client.get("/api/career-plans/31")
        assert result_response.status_code == 200
        assert result_response.json()["data"]["retrieval_source"] == "qdrant_vector"
        assert result_response.json()["data"]["retrieved_chunk_ids"] == ["chunk-1"]

        # get_plan applies both plan_id and current user_id; another user's plan is hidden as 404.
        assert client.get("/api/career-plans/999").status_code == 404


@pytest.mark.asyncio
async def test_start_plan_commits_before_worker_launch(monkeypatch):
    profile = SimpleNamespace(
        id=41,
        user_id=7,
        education="本科",
        experience="1-3年",
        skills=["Python"],
        work_description="后端开发",
        weekly_learning_hours=8,
        preferred_target_role="Python后端工程师",
        projects=[],
    )

    class StartSession:
        committed = False

        async def flush(self):
            return None

        async def commit(self):
            self.committed = True

    db = StartSession()

    async def get_profile(db, profile_id, user_id):
        return profile

    async def count_active(db, user_id):
        return 0

    async def create_plan(db, plan):
        plan.id = 51
        return plan

    async def create_task(db, task):
        return task

    def launch(task_id):
        assert db.committed is True
        assert task_id

    monkeypatch.setattr(service, "get_profile", get_profile)
    monkeypatch.setattr(service, "count_active_tasks_for_user", count_active)
    monkeypatch.setattr(service, "create_plan", create_plan)
    monkeypatch.setattr(service, "create_ai_task", create_task)
    monkeypatch.setattr(service, "launch_ai_task_worker", launch)

    result = await service.start_career_plan(
        db,
        user_id=7,
        request=CareerPlanCreateRequest(profile_id=41),
    )
    assert result.plan.id == 51
    assert result.task.resource_id == 51
    assert result.plan.task_id == result.task.id


class FakeSession:
    def __init__(self, task, plan):
        self.task = task
        self.plan = plan
        self.commits = []

    async def commit(self):
        self.commits.append((self.task.status, self.task.progress, self.plan.status))

    async def flush(self):
        return None


def fake_session_factory(session):
    @asynccontextmanager
    async def factory():
        yield session

    return factory


def build_worker_records():
    task = SimpleNamespace(
        id="career-task-2",
        user_id=7,
        status="pending",
        progress=0,
        result_id=None,
        request_payload={},
        token_usage=None,
        error_message=None,
        started_at=None,
        finished_at=None,
        provider_call_started_at=None,
    )
    plan = SimpleNamespace(
        id=32,
        profile_id=12,
        status="processing",
        error_message=None,
        retrieval_source=None,
        retrieval_error=None,
        retrieved_chunk_ids=None,
        knowledge_base_version=None,
    )
    profile = SimpleNamespace(
        id=12,
        education="本科",
        experience="1-3年",
        skills=["Python"],
        work_description="后端开发",
        weekly_learning_hours=8,
        preferred_target_role="Python后端工程师",
        projects=[],
    )
    return task, plan, profile


async def install_worker_fakes(monkeypatch, session, task, plan, profile):
    async def get_task(db, task_id):
        return task if task.id == task_id else None

    async def get_task_plan(db, task_id):
        return plan if task.id == task_id else None

    async def get_owned_profile(db, profile_id, user_id):
        return profile if (profile_id, user_id) == (profile.id, task.user_id) else None

    async def get_attachments(db, attachment_ids, user_id):
        return []

    async def claim(db, claimed_task, now):
        claimed_task.provider_call_started_at = now

    async def update_task(db, task_id, **values):
        for key, value in values.items():
            setattr(task, key, value)
        return task

    monkeypatch.setattr("app.core.database.async_session", fake_session_factory(session))
    monkeypatch.setattr(service, "get_ai_task", get_task)
    monkeypatch.setattr(service, "get_plan_by_task", get_task_plan)
    monkeypatch.setattr(service, "get_profile", get_owned_profile)
    monkeypatch.setattr(service, "get_project_attachments", get_attachments)
    monkeypatch.setattr(service, "claim_provider_call", claim)
    monkeypatch.setattr(service, "update_ai_task", update_task)
    monkeypatch.setattr("app.core.config.settings.TENCENT_MAAS_API_KEY", "test-key")


@pytest.mark.asyncio
async def test_career_worker_success_persists_result_id_usage_and_retrieval_audit(monkeypatch):
    task, plan, profile = build_worker_records()
    session = FakeSession(task, plan)
    await install_worker_fakes(monkeypatch, session, task, plan, profile)

    async def generate(**kwargs):
        return (
            {},
            {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30, "usage_reported": True},
            {
                "retrieval_source": "qdrant_vector",
                "retrieval_error": None,
                "retrieved_chunk_ids": ["chunk-1"],
                "knowledge_base_version": "v1",
            },
        )

    monkeypatch.setattr(service, "build_generated_career_plan", generate)
    await service.execute_career_plan_task(task.id)

    assert task.status == "success"
    assert task.result_id == plan.id
    assert task.token_usage["total_tokens"] == 30
    assert task.provider_call_started_at is not None
    assert plan.status == "completed"
    assert plan.retrieval_source == "qdrant_vector"
    assert plan.retrieved_chunk_ids == ["chunk-1"]
    assert ("preparing", 10, "processing") in session.commits
    assert ("generating", 35, "processing") in session.commits
    assert ("success", 100, "completed") in session.commits


@pytest.mark.asyncio
async def test_career_worker_failure_writes_task_and_plan_failure(monkeypatch):
    task, plan, profile = build_worker_records()
    session = FakeSession(task, plan)
    await install_worker_fakes(monkeypatch, session, task, plan, profile)

    async def fail_generation(**kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(service, "build_generated_career_plan", fail_generation)
    with pytest.raises(RuntimeError, match="provider unavailable"):
        await service.execute_career_plan_task(task.id)

    assert task.status == "failed"
    assert task.progress == 100
    assert task.finished_at is not None
    assert plan.status == "failed"
    assert plan.error_message == "provider unavailable"
    assert ("failed", 100, "failed") in session.commits
