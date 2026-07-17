import json
from pathlib import Path

import pytest

from app.ai.knowledge import (
    KnowledgeChunk,
    PythonBackendInterviewKnowledgeRetriever,
    SecretaryInterviewKnowledgeRetriever,
    load_knowledge_chunks,
)
from app.ai.mock_interview_agent import MockInterviewAgent
from app.ai.tencent_maas import TextGenerationResult
from app.schemas.mock_interview import MockInterviewCreateRequest


class FakeRetriever:
    last_source = "qdrant_vector"
    last_error = None
    last_results = [{"chunk_id": "interview-1", "source_file": "评分标准.md"}]

    async def retrieve(self, query, *, top_k=None, filters=None):
        return [KnowledgeChunk(
            id="interview-1", document_id="doc", title="面试标准", section="评分",
            content="评分采用专业知识、分析、实践证据和沟通结构四个维度。",
            source_file="评分标准.md", version="v1",
        )]


class FakeGateway:
    def __init__(self, payload):
        self.payload = payload

    async def generate_json(self, **kwargs):
        assert "合法 JSON" in kwargs["system_prompt"]
        return TextGenerationResult(
            content=json.dumps(self.payload, ensure_ascii=False),
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            model_name="fake-model",
        )


def question_payload():
    return {"questions": [
        {
            "question_type": "technical",
            "question": f"请说明 FastAPI 异步接口设计要点 {index}",
            "intent": "考察异步与接口设计",
            "difficulty": "middle",
            "reference_points": ["事件循环", "阻塞调用隔离"],
            "rubric": {"excellent": "覆盖边界和实践"},
        }
        for index in range(1, 4)
    ]}


def test_two_interview_knowledge_bases_have_content():
    python_chunks = load_knowledge_chunks(Path("knowledge_base/interview_python_backend/source"))
    secretary_chunks = load_knowledge_chunks(Path("knowledge_base/interview_secretary_studies/source"))
    assert python_chunks and any("FastAPI" in chunk.content for chunk in python_chunks)
    assert secretary_chunks and any("公文" in chunk.content for chunk in secretary_chunks)


@pytest.mark.asyncio
async def test_two_interview_retrievers_work_locally(monkeypatch):
    monkeypatch.setattr("app.ai.knowledge.settings.QDRANT_ENABLED", False)
    python_chunks = await PythonBackendInterviewKnowledgeRetriever().retrieve("FastAPI 异步事务", top_k=2)
    secretary_chunks = await SecretaryInterviewKnowledgeRetriever().retrieve("会议纪要 公文 保密", top_k=2)
    assert python_chunks
    assert secretary_chunks


@pytest.mark.asyncio
async def test_langgraph_interviewer_generates_valid_questions():
    agent = MockInterviewAgent(
        domain="python_backend", gateway=FakeGateway(question_payload()), retriever=FakeRetriever()
    )
    state = await agent.run(mode="questions", context={
        "domain": "python_backend", "target_role": "Python后端开发工程师",
        "job_description": "FastAPI开发", "resume_text": "Python项目",
        "difficulty": "middle", "question_types": ["technical"], "question_count": 3,
    })
    assert len(state["result"].questions) == 3
    assert state["retrieval_source"] == "qdrant_vector"
    assert state["token_usage"]["total_tokens"] == 30


def test_applied_source_requires_job_and_supported_routes_registered():
    with pytest.raises(ValueError):
        MockInterviewCreateRequest(
            source_type="applied", difficulty="middle",
            question_types=["technical"], question_count=3,
        )
    from app.main import app

    paths = app.openapi()["paths"]
    assert "/api/interviews/options" in paths
    assert "/api/interviews" in paths
    assert "/api/interviews/{interview_id}/answer" in paths
    assert "/api/interviews/{interview_id}/finish" in paths
    assert "/api/interviews/{interview_id}/report" in paths
    assert "/api/interviews/{interview_id}/retry" in paths
