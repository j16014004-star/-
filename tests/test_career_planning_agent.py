import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.ai.career_planning_agent import CareerPlanningAgent
from app.ai.career_planning_prompt import SYSTEM_PROMPT
from app.ai.knowledge import CareerKnowledgeRetriever, KnowledgeChunk, load_knowledge_chunks
from app.ai.tencent_maas import TextGenerationResult
from app.schemas.career_plan import CareerPlanAIOutput


def build_plan_payload() -> dict:
    return {
        "career_profile_summary": {
            "current_stage": "1-3年 · 本科",
            "core_strengths": ["Python", "FastAPI", "SQL"],
            "transferable_skills": ["问题分析", "沟通协作"],
            "main_weaknesses": ["缺少部署链接", "项目成果需要量化"],
            "summary": "建议以 Python 后端工程师作为主线方向。",
        },
        "recommended_roles": [
            {
                "role_name": "Python 后端工程师",
                "match_score": 86,
                "priority": 1,
                "recommendation_reason": "与 FastAPI 和 SQL 项目经验匹配。",
                "matched_capabilities": ["Python", "FastAPI"],
                "missing_capabilities": ["Redis", "Docker"],
                "suitable_industries": ["AI应用", "企业服务"],
                "next_actions": ["补充部署文档", "增加接口测试"],
                "is_long_term_direction": True,
            }
        ],
        "career_goals": {
            "short_term": ["补齐项目 README"],
            "medium_term": ["完成可部署作品"],
            "long_term": ["提升系统设计能力"],
        },
        "skill_gap_analysis": [
            {
                "skill": "Redis",
                "priority": "high",
                "current_level": "待补充",
                "target_level": "能说明缓存和任务状态场景",
                "reason": "Python 后端岗位常见要求。",
            }
        ],
        "learning_path": {
            "total_weeks": 12,
            "hours_per_week": 8,
            "stages": [
                {
                    "stage": "后端基础补齐",
                    "duration": "第1-3周",
                    "goals": ["掌握 FastAPI 接口规范"],
                    "topics": ["FastAPI", "SQLAlchemy"],
                    "tasks": ["整理 10 个目标岗位 JD"],
                    "practice_tasks": ["补充接口测试"],
                    "deliverables": ["接口文档"],
                    "acceptance_criteria": ["能讲清接口鉴权流程"],
                }
            ],
        },
        "action_plan": {
            "this_week": ["整理项目亮点"],
            "this_month": ["部署项目到服务器"],
            "portfolio_projects": ["完善 AI 求职助手后端"],
            "resume_actions": ["突出 FastAPI 和 worker"],
            "review_points": ["每周复盘投递反馈"],
        },
        "risks_and_alternatives": {
            "risks": ["目标岗位过多导致学习分散"],
            "assumptions_to_confirm": ["每周可投入 8 小时"],
            "alternative_roles": ["AI 应用后端工程师"],
            "adjustment_advice": ["优先聚焦 Python 后端主线"],
        },
    }


def test_career_knowledge_document_is_chunked():
    chunks = load_knowledge_chunks(Path("knowledge_base/career_planning/source"))
    assert chunks
    assert any("Python 后端工程师" in chunk.content for chunk in chunks)
    assert all(chunk.content for chunk in chunks)


@pytest.mark.asyncio
async def test_career_knowledge_retriever_local_returns_python_backend_chunk(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.QDRANT_ENABLED", False)
    chunks = await CareerKnowledgeRetriever().retrieve("Python 后端工程师 FastAPI Redis Docker 求职", top_k=3)
    assert chunks
    assert any("FastAPI" in chunk.content or "Python 后端工程师" in chunk.content for chunk in chunks)


@pytest.mark.asyncio
async def test_career_retriever_records_qdrant_fallback_reason(monkeypatch):
    retriever = CareerKnowledgeRetriever()

    async def fail_qdrant(query, limit):
        raise RuntimeError("qdrant unavailable")

    monkeypatch.setattr("app.core.config.settings.QDRANT_ENABLED", True)
    monkeypatch.setattr(retriever, "_retrieve_qdrant", fail_qdrant)
    chunks = await retriever.retrieve("Python FastAPI", top_k=1)

    assert chunks
    assert retriever.last_source == "local_keyword_fallback"
    assert retriever.last_error == "Qdrant retrieval failed: RuntimeError"


def test_career_plan_ai_output_requires_complete_schema():
    payload = build_plan_payload()
    CareerPlanAIOutput.model_validate(payload)
    payload.pop("action_plan")
    with pytest.raises(ValidationError):
        CareerPlanAIOutput.model_validate(payload)


class FakeCareerGateway:
    async def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model_name: str | None = None,
        max_tokens: int | None = None,
    ):
        assert "职业生涯规划 Agent" in system_prompt
        assert "career_planning_context" in user_prompt
        assert model_name
        return TextGenerationResult(
            content=json.dumps(build_plan_payload(), ensure_ascii=False),
            usage={"total_tokens": 88},
        )


class FakeCareerRetriever:
    async def retrieve(self, query: str, *, top_k: int | None = None):
        assert "Python 后端工程师" in query
        return [
            KnowledgeChunk(
                id="career-1",
                document_id="doc-1",
                title="Python后端工程师职业规划指南",
                section="必备技术栈",
                content="Python 后端工程师需要 FastAPI、SQLAlchemy、Redis、Docker 和 pytest。",
                source_file="Python后端工程师职业规划指南.md",
                version="v1",
            )
        ]


@pytest.mark.asyncio
async def test_career_planning_agent_runs_without_real_cloud_call():
    agent = CareerPlanningAgent(gateway=FakeCareerGateway(), retriever=FakeCareerRetriever())
    state = await agent.run(
        profile={
            "education": "bachelor",
            "experience": "1-3",
            "skills": ["Python", "FastAPI", "SQL"],
            "work_description": "负责后端接口开发",
            "weekly_learning_hours": 8,
            "preferred_target_role": "Python 后端工程师",
            "projects": [{"name": "AI求职助手", "description": "FastAPI 后端", "role": "后端开发"}],
        },
        project_attachments=[],
        request_payload={"preferred_target_role": "Python 后端工程师"},
    )
    assert state["result"].recommended_roles[0].role_name == "Python 后端工程师"
    assert state["token_usage"]["total_tokens"] == 88
    assert state["retrieval_source"] == "unknown"
    assert state["retrieved_chunk_ids"] == ["career-1"]
    assert "JSON" in SYSTEM_PROMPT


def test_career_routes_are_registered():
    from app.main import app

    paths = app.openapi()["paths"]
    assert "/api/career-planning/profiles" in paths
    assert "/api/career-plans" in paths
    assert "/api/career-plans/{plan_id}" in paths
    assert "/api/career-plans/project-files/upload" in paths
    assert "/api/career-plans/project-files/{file_id}" in paths
