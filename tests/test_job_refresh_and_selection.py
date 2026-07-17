from types import SimpleNamespace

import pytest

from app.services import job_refresh_service, recommendation_start_service
from app.schemas.job_recommendation import PlatformLoginStartRequest
from app.schemas.job import JobApplyRequest
from pydantic import ValidationError


class FakeDB:
    async def execute(self, _query):
        return SimpleNamespace()

    async def flush(self):
        return None


class ForceRefreshDB(FakeDB):
    def __init__(self):
        self.cancelled_active_task = False

    async def execute(self, query):
        if getattr(query, "is_update", False):
            self.cancelled_active_task = True
        return SimpleNamespace()


@pytest.mark.asyncio
async def test_selected_role_and_city_are_used_to_build_new_task(monkeypatch):
    session = SimpleNamespace(id="session-1", source="58", status="waiting_login")
    resume = SimpleNamespace(
        id=9,
        status="completed",
        structured_data={"city": "北京"},
        extracted_text="技能：Python FastAPI",
    )

    async def none(*_args, **_kwargs):
        return None

    async def get_session(*_args, **_kwargs):
        return session

    async def get_resume(*_args, **_kwargs):
        return resume

    async def create(_db, task):
        return task

    monkeypatch.setattr(recommendation_start_service, "get_login_session", get_session)
    monkeypatch.setattr(recommendation_start_service, "get_latest_recommend_task_by_login_session", none)
    monkeypatch.setattr(recommendation_start_service, "get_active_recommend_task", none)
    monkeypatch.setattr(recommendation_start_service, "get_resume_by_id", get_resume)
    monkeypatch.setattr(recommendation_start_service, "get_resume_skills", lambda *_: ["Python", "FastAPI"])
    monkeypatch.setattr(recommendation_start_service, "create_recommend_task", create)

    result = await recommendation_start_service.ensure_recommendation_task(
        FakeDB(),
        user_id=7,
        resume_id=9,
        source="58",
        login_session_id="session-1",
        target_role="Python后端开发工程师",
        target_city="西安",
        launch_if_ready=False,
    )

    assert result.task.target_role == "Python后端开发工程师"
    assert result.task.target_city == "西安"
    assert result.task.search_keywords[0] == "Python后端开发工程师"


@pytest.mark.asyncio
async def test_force_refresh_reuses_active_task_instead_of_cancelling_it(monkeypatch):
    db = ForceRefreshDB()
    session = SimpleNamespace(id="session-1", source="58", status="waiting_login")
    resume = SimpleNamespace(
        id=9, status="completed", structured_data={}, extracted_text="Python FastAPI",
    )
    old_task = SimpleNamespace(
        id="old-task", status="crawling", resume_id=9,
        resume_source="original", resume_optimization_id=None,
    )

    async def get_session(*_args, **_kwargs):
        return session

    async def latest_task(*_args, **_kwargs):
        return None if db.cancelled_active_task else old_task

    async def no_active(*_args, **_kwargs):
        return None

    async def get_resume(*_args, **_kwargs):
        return resume

    async def create(_db, task):
        return task

    monkeypatch.setattr(recommendation_start_service, "get_login_session", get_session)
    monkeypatch.setattr(
        recommendation_start_service,
        "get_latest_recommend_task_by_login_session",
        latest_task,
    )
    monkeypatch.setattr(recommendation_start_service, "get_active_recommend_task", no_active)
    monkeypatch.setattr(recommendation_start_service, "get_resume_by_id", get_resume)
    monkeypatch.setattr(recommendation_start_service, "get_resume_skills", lambda *_: ["Python"])
    monkeypatch.setattr(recommendation_start_service, "create_recommend_task", create)

    result = await recommendation_start_service.ensure_recommendation_task(
        db,
        user_id=7,
        resume_id=9,
        source="58",
        login_session_id="session-1",
        target_role="Python开发",
        target_city="西安",
        launch_if_ready=False,
        force_refresh=True,
    )

    assert db.cancelled_active_task is False
    assert result.created is False
    assert result.task.id == old_task.id


@pytest.mark.asyncio
async def test_unsupported_selected_city_is_rejected_not_silently_changed(monkeypatch):
    session = SimpleNamespace(id="session-1", source="58", status="waiting_login")
    resume = SimpleNamespace(id=9, status="completed", structured_data={}, extracted_text="Python")

    async def none(*_args, **_kwargs):
        return None

    async def get_session(*_args, **_kwargs):
        return session

    async def get_resume(*_args, **_kwargs):
        return resume

    monkeypatch.setattr(recommendation_start_service, "get_login_session", get_session)
    monkeypatch.setattr(recommendation_start_service, "get_latest_recommend_task_by_login_session", none)
    monkeypatch.setattr(recommendation_start_service, "get_active_recommend_task", none)
    monkeypatch.setattr(recommendation_start_service, "get_resume_by_id", get_resume)
    monkeypatch.setattr(recommendation_start_service, "get_resume_skills", lambda *_: ["Python"])

    with pytest.raises(recommendation_start_service.RecommendationStartError, match="暂不支持所选城市"):
        await recommendation_start_service.ensure_recommendation_task(
            FakeDB(), user_id=7, resume_id=9, source="58", login_session_id="session-1",
            target_role="Python开发", target_city="火星", launch_if_ready=False,
        )


@pytest.mark.asyncio
async def test_new_resume_refresh_reuses_last_user_selection(monkeypatch):
    session = SimpleNamespace(id="session-1", status="logged_in", error_message=None)
    previous = SimpleNamespace(
        requested_limit=30,
        target_role="厨师",
        target_city="西安",
    )
    captured = {}

    async def latest_session(*_args, **_kwargs):
        return session

    async def latest_task(*_args, **_kwargs):
        return previous

    async def ensure(*_args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(task=SimpleNamespace(id="new-task", status="pending"))

    monkeypatch.setattr(job_refresh_service, "get_latest_login_session", latest_session)
    monkeypatch.setattr(job_refresh_service, "get_latest_recommend_task", latest_task)
    monkeypatch.setattr(job_refresh_service, "is_login_state_ready", lambda *_: True)
    monkeypatch.setattr(job_refresh_service, "ensure_recommendation_task", ensure)

    result = await job_refresh_service.trigger_refresh_for_new_resume(
        FakeDB(), user_id=7, resume=SimpleNamespace(id=10),
    )

    assert result["task_id"] == "new-task"
    assert captured["resume_id"] == 10
    assert captured["target_role"] == "厨师"
    assert captured["target_city"] == "西安"
    assert captured["limit"] == 30


def test_optimized_resume_request_requires_version_id():
    with pytest.raises(ValidationError):
        PlatformLoginStartRequest(
            source="58", resume_id=7, resume_source="optimized",
            target_role="Java开发工程师", target_city="西安",
        )
    with pytest.raises(ValidationError):
        JobApplyRequest(resume_id=7, resume_source="optimized")


@pytest.mark.asyncio
async def test_optimized_resume_uses_saved_final_content_for_skill_extraction(monkeypatch):
    session = SimpleNamespace(id="session-1", source="58", status="waiting_login")
    resume = SimpleNamespace(
        id=9, status="completed", structured_data={"skills": ["Python"]},
        extracted_text="Python FastAPI",
    )
    version = SimpleNamespace(
        id=26, resume_id=9, optimized_content="Java Spring Boot MySQL",
        target_role="Java开发工程师",
    )

    async def none(*_args, **_kwargs):
        return None

    async def get_session(*_args, **_kwargs):
        return session

    async def get_resume(*_args, **_kwargs):
        return resume

    async def get_version(*_args, **_kwargs):
        return version

    async def create(_db, task):
        return task

    def extract_skills(structured_data, text):
        assert structured_data is None
        assert text == version.optimized_content
        return ["Java", "Spring Boot", "MySQL"]

    monkeypatch.setattr(recommendation_start_service, "get_login_session", get_session)
    monkeypatch.setattr(recommendation_start_service, "get_latest_recommend_task_by_login_session", none)
    monkeypatch.setattr(recommendation_start_service, "get_active_recommend_task", none)
    monkeypatch.setattr(recommendation_start_service, "get_resume_by_id", get_resume)
    monkeypatch.setattr(recommendation_start_service, "get_owned_saved_optimization_version", get_version)
    monkeypatch.setattr(recommendation_start_service, "get_resume_skills", extract_skills)
    monkeypatch.setattr(recommendation_start_service, "create_recommend_task", create)

    result = await recommendation_start_service.ensure_recommendation_task(
        FakeDB(), user_id=7, resume_id=9, source="58", login_session_id="session-1",
        resume_source="optimized", resume_optimization_id=26,
        target_role="Java开发工程师", target_city="西安", launch_if_ready=False,
    )

    assert result.task.resume_source == "optimized"
    assert result.task.resume_optimization_id == 26
    assert result.task.extracted_skills == ["Java", "Spring Boot", "MySQL"]
