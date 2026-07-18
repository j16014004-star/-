from datetime import datetime
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.routers import job_platforms as router_module
from app.schemas.job_recommendation import LoginSessionResponse


NOW = datetime(2026, 7, 16, 18, 0, 0)


def test_login_response_schema_accepts_remote_browser_url():
    value = LoginSessionResponse(
        login_session_id="session-1",
        source="58",
        source_name="58同城",
        status="waiting_login",
        login_mode="remote_browser",
        login_url="https://passport.58.com/login",
        browser_url="https://example.com/browser",
        expires_at=NOW,
    )
    assert value.login_mode == "remote_browser"
    assert value.browser_url == "https://example.com/browser"


def test_server_headless_login_fails_fast_without_remote_browser(monkeypatch):
    async def get_resume(*_args, **_kwargs):
        return SimpleNamespace(id=9, status="completed")

    monkeypatch.setattr(router_module, "get_resume_by_id", get_resume)
    monkeypatch.setattr(router_module.settings, "PLAYWRIGHT_CDP_ENDPOINT", "")
    monkeypatch.setattr(router_module.settings, "PLAYWRIGHT_HEADLESS", True)
    response = TestClient(build_app()).post(
        "/api/job-platforms/login/start",
        json={
            "source": "58",
            "resume_id": 9,
            "resume_source": "original",
            "target_role": "Python后端开发工程师",
            "target_city": "西安",
        },
    )
    assert response.status_code == 503
    assert "可视化远程浏览器" in response.json()["detail"]


def build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router_module.router)

    async def fake_db():
        yield SimpleNamespace()

    async def fake_user():
        return SimpleNamespace(id=7)

    app.dependency_overrides[get_db] = fake_db
    app.dependency_overrides[get_current_user] = fake_user
    return app


def task(status: str = "success") -> SimpleNamespace:
    return SimpleNamespace(
        id="task-1",
        login_session_id="session-1",
        status=status,
        progress=100,
        source="58",
        resume_id=9,
        resume_source="original",
        resume_optimization_id=None,
        target_role="Python后端开发工程师",
        target_city="北京",
        extracted_skills=["Python", "FastAPI"],
        search_keywords=["Python后端开发", "Python开发工程师"],
        total_found=2,
        total_saved=2,
        total_matched=2 if status == "success" else 0,
        failure_code=None if status == "success" else "no_exact_results",
        error_message=None if status == "success" else "暂无精准岗位",
        crawl_diagnostics={"raw_items": 2, "accepted_items": 2},
        created_at=NOW,
        started_at=NOW,
        finished_at=NOW,
    )


def test_current_task_endpoint_restores_latest_task(monkeypatch):
    async def get_resume(*_args, **_kwargs):
        return SimpleNamespace(id=9)

    async def get_latest(*_args, **_kwargs):
        return task()

    monkeypatch.setattr(router_module, "get_resume_by_id", get_resume)
    monkeypatch.setattr(router_module, "get_latest_recommend_task", get_latest)

    response = TestClient(build_app()).get("/api/jobs/recommend/current?resume_id=9&source=58")
    assert response.status_code == 200
    payload = response.json()["data"]["task"]
    assert payload["task_id"] == "task-1"
    assert payload["target_role"] == "Python后端开发工程师"
    assert payload["resume_source"] == "original"
    assert payload["resume_optimization_id"] is None
    assert payload["search_keywords"] == ["Python后端开发", "Python开发工程师"]
    assert payload["crawl_diagnostics"]["accepted_items"] == 2


def test_no_results_task_returns_empty_result_page_instead_of_conflict(monkeypatch):
    no_results = task("no_results")

    async def get_owned_task(*_args, **_kwargs):
        return no_results

    monkeypatch.setattr(router_module, "get_recommend_task", get_owned_task)
    response = TestClient(build_app()).get(
        "/api/jobs/recommend/tasks/task-1/results?page=1&page_size=20"
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["task_id"] == "task-1"
    assert payload["total"] == 0
    assert payload["items"] == []
    assert payload["target_city"] == "北京"


def test_cross_user_or_missing_task_is_404(monkeypatch):
    async def missing(*_args, **_kwargs):
        return None

    monkeypatch.setattr(router_module, "get_recommend_task", missing)
    response = TestClient(build_app()).get("/api/jobs/recommend/tasks/not-owned")
    assert response.status_code == 404


def test_current_task_filters_exact_optimized_resume_version(monkeypatch):
    captured = {}

    async def get_resume(*_args, **_kwargs):
        return SimpleNamespace(id=9)

    async def get_latest(*args, **_kwargs):
        captured["args"] = args
        value = task()
        value.resume_source = "optimized"
        value.resume_optimization_id = 26
        return value

    monkeypatch.setattr(router_module, "get_resume_by_id", get_resume)
    monkeypatch.setattr(router_module, "get_latest_recommend_task", get_latest)
    response = TestClient(build_app()).get(
        "/api/jobs/recommend/current?resume_id=9&resume_source=optimized&resume_optimization_id=26&source=58"
    )
    assert response.status_code == 200
    assert captured["args"][-2:] == ("optimized", 26)
    assert response.json()["data"]["task"]["resume_optimization_id"] == 26
