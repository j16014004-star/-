import json
from contextlib import asynccontextmanager
from datetime import datetime
from types import SimpleNamespace

import pytest

from app.ai.career_question_agent import CareerQuestionAgent
from app.ai.knowledge import KnowledgeChunk
from app.ai.tencent_maas import TextGenerationResult
from app.schemas.career_plan import CareerQuestionAIOutput, CareerQuestionRequest
from app.services import career_question_service as service
from app.services.career_plan_service import CareerPlanError


NOW = datetime(2026, 7, 16, 15, 0, 0)


class FakeQuestionGateway:
    async def generate_json(self, *, system_prompt, user_prompt, model_name=None, max_tokens=None):
        assert "答疑 Agent" in system_prompt
        assert "FastAPI Depends" in user_prompt
        assert "当前练习" in user_prompt
        assert model_name
        assert max_tokens == 2000
        return TextGenerationResult(
            content=json.dumps({"answer": "Depends 用于声明依赖。步骤：定义依赖函数并在路由参数中使用。"}, ensure_ascii=False),
            usage={"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
        )


class FakeQuestionRetriever:
    last_source = "qdrant_vector"
    last_error = None

    async def retrieve(self, query, *, top_k=None, filters=None):
        assert "FastAPI Depends" in query
        return [KnowledgeChunk(
            id="question-chunk-1",
            document_id="doc-1",
            title="FastAPI",
            section="依赖注入",
            content="Depends 用于声明 FastAPI 依赖。",
            source_file="career.md",
            version="v1",
        )]


@pytest.mark.asyncio
async def test_career_question_agent_uses_task_plan_and_knowledge_context():
    agent = CareerQuestionAgent(
        gateway=FakeQuestionGateway(), retriever=FakeQuestionRetriever()
    )
    state = await agent.run(
        question="FastAPI Depends 应该怎么使用？",
        task_context={"title": "当前练习", "stage": "基础巩固", "week_no": 1},
        plan_context={"recommended_roles": [{"role_name": "Python后端工程师"}]},
    )
    assert state["result"].answer.startswith("Depends")
    assert state["retrieval_source"] == "qdrant_vector"
    assert state["retrieved_chunk_ids"] == ["question-chunk-1"]
    assert state["token_usage"]["total_tokens"] == 30


def test_sensitive_values_are_redacted_but_concept_questions_are_preserved():
    safe, redacted = service.redact_sensitive_text("我的 API_KEY=abcdef123456，请帮我检查")
    assert redacted is True
    assert "abcdef123456" not in safe
    conceptual, conceptual_redacted = service.redact_sensitive_text("密码是什么，应该如何安全保存？")
    assert conceptual_redacted is False
    assert conceptual == "密码是什么，应该如何安全保存？"


class SubmitDb:
    def __init__(self):
        self.committed = False

    async def execute(self, statement):
        return None

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_submit_question_is_idempotent_and_does_not_store_secret_in_task_payload(monkeypatch):
    db = SubmitDb()
    execution_task = SimpleNamespace(id=71, execution_plan_id=61)
    execution = SimpleNamespace(id=61, career_plan_id=51)
    plan = SimpleNamespace(id=51)
    created_question = None
    created_task = None
    launches = []

    async def get_task(db, task_id, user_id):
        return execution_task

    async def get_execution(db, execution_id, user_id):
        return execution

    async def get_plan(db, plan_id, user_id):
        return plan

    async def reusable(db, **kwargs):
        return created_question

    async def get_ai_task(db, task_id):
        return created_task

    async def active_count(db, user_id):
        return 0

    async def latest(db, user_id):
        return None

    async def create_question(db, question):
        nonlocal created_question
        question.id = 81
        question.created_at = NOW
        created_question = question
        return question

    async def create_ai_task(db, task):
        nonlocal created_task
        created_task = task
        return task

    def launch(task_id):
        assert db.committed is True
        launches.append(task_id)

    monkeypatch.setattr(service, "get_owned_execution_task", get_task)
    monkeypatch.setattr(service, "get_execution_by_id", get_execution)
    monkeypatch.setattr(service, "get_plan", get_plan)
    monkeypatch.setattr(service, "get_reusable_question", reusable)
    monkeypatch.setattr(service, "get_ai_task", get_ai_task)
    monkeypatch.setattr(service, "count_active_tasks_for_user", active_count)
    monkeypatch.setattr(service, "get_latest_user_question", latest)
    monkeypatch.setattr(service, "create_question", create_question)
    monkeypatch.setattr(service, "create_ai_task", create_ai_task)
    monkeypatch.setattr(service, "launch_ai_task_worker", launch)

    request = CareerQuestionRequest(question="我的 API_KEY=abcdef123456，FastAPI Depends 怎么使用？")
    first = await service.submit_career_question(
        db, user_id=7, execution_task_id=71, request=request
    )
    second = await service.submit_career_question(
        db, user_id=7, execution_task_id=71, request=request
    )

    assert first.task.id == second.task.id
    assert len(launches) == 1
    assert "abcdef123456" not in first.question.question
    assert first.question.sensitive_redacted is True
    assert first.task.request_payload == {"question_id": 81, "execution_task_id": 71}


class WorkerDb:
    async def commit(self):
        return None

    async def flush(self):
        return None


def session_factory(db):
    @asynccontextmanager
    async def factory():
        yield db

    return factory


def build_worker_context():
    task = SimpleNamespace(
        id="question-task-1",
        user_id=7,
        resource_id=81,
        status="pending",
        progress=0,
        result_id=None,
        token_usage=None,
        error_message=None,
        started_at=None,
        finished_at=None,
        provider_call_started_at=None,
    )
    question = SimpleNamespace(
        id=81,
        user_id=7,
        execution_task_id=71,
        question="FastAPI Depends 怎么使用？",
        answer=None,
        status="pending",
        error_message=None,
        sensitive_redacted=False,
        retrieval_source=None,
        retrieval_error=None,
        retrieved_chunk_ids=None,
        knowledge_base_version=None,
        answered_at=None,
    )
    execution_task = SimpleNamespace(
        id=71,
        execution_plan_id=61,
        title="完成 FastAPI 依赖注入练习",
        description="实现三个接口",
        task_type="practice",
        stage="基础巩固",
        week_no=1,
        status="pending",
    )
    execution = SimpleNamespace(id=61, career_plan_id=51)
    plan = SimpleNamespace(
        id=51,
        profile_id=41,
        status="accepted",
        accepted_at=NOW,
        previous_plan_id=None,
        career_profile_summary={},
        recommended_roles=[],
        career_goals={},
        skill_gap_analysis=[],
        learning_path={},
        action_plan={},
        risks_and_alternatives={},
        retrieval_source="qdrant_vector",
        retrieval_error=None,
        retrieved_chunk_ids=[],
        knowledge_base_version="v1",
        created_at=NOW,
    )
    return task, question, execution_task, execution, plan


async def install_worker_fakes(monkeypatch, db, task, question, execution_task, execution, plan):
    async def get_ai_task(db, task_id):
        return task

    async def get_question(db, question_id):
        return question

    async def get_execution_task(db, task_id, user_id):
        return execution_task

    async def get_execution(db, execution_id, user_id):
        return execution

    async def get_plan(db, plan_id, user_id):
        return plan

    async def claim(db, claimed_task, now):
        claimed_task.provider_call_started_at = now

    async def update(db, task_id, **values):
        for key, value in values.items():
            setattr(task, key, value)
        return task

    monkeypatch.setattr("app.core.database.async_session", session_factory(db))
    monkeypatch.setattr(service, "get_ai_task", get_ai_task)
    monkeypatch.setattr(service, "get_question", get_question)
    monkeypatch.setattr(service, "get_owned_execution_task", get_execution_task)
    monkeypatch.setattr(service, "get_execution_by_id", get_execution)
    monkeypatch.setattr(service, "get_plan", get_plan)
    monkeypatch.setattr(service, "claim_provider_call", claim)
    monkeypatch.setattr(service, "update_ai_task", update)
    monkeypatch.setattr("app.core.config.settings.TENCENT_MAAS_API_KEY", "test-key")


@pytest.mark.asyncio
async def test_question_worker_saves_answer_usage_audit_and_result_id(monkeypatch):
    db = WorkerDb()
    task, question, execution_task, execution, plan = build_worker_context()
    await install_worker_fakes(
        monkeypatch, db, task, question, execution_task, execution, plan
    )

    class FakeAgent:
        async def run(self, **kwargs):
            return {
                "result": CareerQuestionAIOutput(answer="Depends 用于声明依赖。"),
                "token_usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                "knowledge_chunks": [SimpleNamespace(version="v1")],
                "retrieval_source": "qdrant_vector",
                "retrieval_error": None,
                "retrieved_chunk_ids": ["chunk-1"],
            }

    monkeypatch.setattr(service, "CareerQuestionAgent", FakeAgent)
    await service.execute_career_question_task(task.id)

    assert task.status == "success"
    assert task.result_id == question.id
    assert task.token_usage["total_tokens"] == 15
    assert question.status == "answered"
    assert question.answer.startswith("Depends")
    assert question.retrieval_source == "qdrant_vector"
    assert question.retrieved_chunk_ids == ["chunk-1"]


@pytest.mark.asyncio
async def test_question_worker_failure_is_persisted(monkeypatch):
    db = WorkerDb()
    task, question, execution_task, execution, plan = build_worker_context()
    await install_worker_fakes(
        monkeypatch, db, task, question, execution_task, execution, plan
    )

    class FailingAgent:
        async def run(self, **kwargs):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(service, "CareerQuestionAgent", FailingAgent)
    with pytest.raises(RuntimeError, match="provider unavailable"):
        await service.execute_career_question_task(task.id)

    assert task.status == "failed"
    assert task.progress == 100
    assert question.status == "failed"
    assert question.error_message == "provider unavailable"


@pytest.mark.asyncio
async def test_question_history_hides_other_users_task(monkeypatch):
    async def get_task(db, task_id, user_id):
        return None

    monkeypatch.setattr(service, "get_owned_execution_task", get_task)
    with pytest.raises(CareerPlanError) as exc_info:
        await service.list_career_questions(
            WorkerDb(), user_id=8, execution_task_id=71
        )
    assert exc_info.value.status_code == 404
