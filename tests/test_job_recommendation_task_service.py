from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.crawlers.job_58_playwright import JobPageParseError
from app.services import recommendation_task_service as service


class ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalar_one(self):
        return self.value


class FakeDB:
    def __init__(self, values):
        self.values = list(values)

    async def execute(self, _query):
        return ScalarResult(self.values.pop(0))

    async def commit(self):
        return None


def build_task_and_login(state_path: Path):
    task = SimpleNamespace(
        id="task-1",
        source="58",
        user_id=7,
        resume_id=9,
        login_session_id="login-1",
        target_role="Python后端开发工程师",
        target_city="北京",
        extracted_skills=["Python", "FastAPI"],
        search_keywords=["Python后端开发", "Python开发工程师"],
        requested_limit=20,
        status="pending",
        progress=0,
        total_found=0,
        total_saved=0,
        total_matched=0,
        failure_code=None,
        error_message=None,
        crawl_diagnostics=None,
        started_at=None,
        finished_at=None,
    )
    login = SimpleNamespace(id="login-1", storage_state_ref=str(state_path))
    return task, login


def test_job_is_deactivated_only_after_two_consecutive_missing_searches():
    first, first_deactivated = service.advance_missing_counts({"26": 0}, set())
    second, second_deactivated = service.advance_missing_counts(first, set())
    restored, restored_deactivated = service.advance_missing_counts(second, {26})

    assert first == {"26": 1}
    assert first_deactivated == []
    assert second == {"26": 2}
    assert second_deactivated == [26]
    assert restored == {"26": 0}
    assert restored_deactivated == []


@pytest.mark.asyncio
async def test_empty_crawl_is_no_results_never_success(monkeypatch, tmp_path):
    state_path = tmp_path / "58.json"
    state_path.write_text("{}", encoding="utf-8")
    task, login = build_task_and_login(state_path)
    fake_db = FakeDB([task, login, task])

    @asynccontextmanager
    async def fake_session():
        yield fake_db

    async def fake_update(_db, _task_id, **values):
        for key, value in values.items():
            setattr(task, key, value)
        return task

    class EmptyCrawler:
        last_diagnostics = {"query_count": 2, "raw_items": 0, "accepted_items": 0}

        async def crawl(self, *_args, **_kwargs):
            return []

    monkeypatch.setattr(service, "async_session", fake_session)
    monkeypatch.setattr(service, "update_task", fake_update)
    monkeypatch.setattr(service, "Job58PlaywrightCrawler", EmptyCrawler)
    async def fake_reconcile(_db, *, task, seen_job_ids, diagnostics):
        return diagnostics
    monkeypatch.setattr(service, "reconcile_job_freshness", fake_reconcile)

    await service.run_recommendation_task(task.id)

    assert task.status == "no_results"
    assert task.progress == 100
    assert task.failure_code == "no_exact_results"
    assert task.total_matched == 0
    assert task.crawl_diagnostics["query_count"] == 2


@pytest.mark.asyncio
async def test_parser_failure_has_explicit_failure_code(monkeypatch, tmp_path):
    state_path = tmp_path / "58.json"
    state_path.write_text("{}", encoding="utf-8")
    task, login = build_task_and_login(state_path)
    fake_db = FakeDB([task, login])

    @asynccontextmanager
    async def fake_session():
        yield fake_db

    async def fake_update(_db, _task_id, **values):
        for key, value in values.items():
            setattr(task, key, value)
        return task

    class BrokenCrawler:
        async def crawl(self, *_args, **_kwargs):
            raise JobPageParseError(
                "检测到35个岗位节点，但未解析出有效岗位",
                {"raw_items": 35, "parsed_items": 0},
            )

    monkeypatch.setattr(service, "async_session", fake_session)
    monkeypatch.setattr(service, "update_task", fake_update)
    monkeypatch.setattr(service, "Job58PlaywrightCrawler", BrokenCrawler)

    await service.run_recommendation_task(task.id)

    assert task.status == "failed"
    assert task.failure_code == "parse_failed"
    assert task.crawl_diagnostics == {"raw_items": 35, "parsed_items": 0}
    assert "35个岗位节点" in task.error_message
