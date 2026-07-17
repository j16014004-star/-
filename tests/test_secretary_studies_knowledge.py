from pathlib import Path

import pytest

from app.ai.career_assessment_agent import CareerAssessmentAgent
from app.ai.career_planning_agent import CareerPlanningAgent
from app.ai.knowledge import (
    CareerKnowledgeRetriever,
    HrCommunicationKnowledgeRetriever,
    JobRecommendationKnowledgeRetriever,
    ResumeKnowledgeRetriever,
    SkillAssessmentKnowledgeRetriever,
    infer_knowledge_role,
    load_knowledge_chunks,
)
from app.core.config import settings
from app.services.job_recommendation_rules import (
    build_search_keywords,
    infer_target_role,
    role_title_terms,
)
from app.services.skills_service import extract_skills_from_text


def test_secretary_professional_domain_is_detected():
    assert infer_knowledge_role("秘书学专业，擅长公文写作") == "secretary_studies"
    assert infer_knowledge_role("Python FastAPI 后端开发") == "python_backend"
    assert infer_knowledge_role("通用求职安全规则") == "general"


@pytest.mark.parametrize(
    "source_dir",
    [
        settings.RESUME_OPTIMIZATION_KB_SOURCE_DIR,
        settings.CAREER_PLANNING_KB_SOURCE_DIR,
        settings.SKILL_ASSESSMENT_KB_SOURCE_DIR,
        settings.JOB_RECOMMENDATION_KB_SOURCE_DIR,
        settings.HR_COMMUNICATION_KB_SOURCE_DIR,
    ],
)
def test_every_module_contains_secretary_knowledge(source_dir):
    chunks = load_knowledge_chunks(Path(source_dir))
    secretary_chunks = [
        chunk for chunk in chunks if chunk.metadata.get("role") == "secretary_studies"
    ]
    assert secretary_chunks
    assert all("Python后端" not in chunk.title for chunk in secretary_chunks)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "retriever_type",
    [
        ResumeKnowledgeRetriever,
        CareerKnowledgeRetriever,
        SkillAssessmentKnowledgeRetriever,
        JobRecommendationKnowledgeRetriever,
        HrCommunicationKnowledgeRetriever,
    ],
)
async def test_secretary_retrieval_isolated_from_python(monkeypatch, retriever_type):
    monkeypatch.setattr(settings, "QDRANT_ENABLED", False)
    chunks = await retriever_type().retrieve(
        "秘书学 行政助理 公文写作 会议纪要 档案管理",
        top_k=4,
        filters={"role": ["secretary_studies", "general"]},
    )
    assert chunks
    assert any(chunk.metadata.get("role") == "secretary_studies" for chunk in chunks)
    assert all(chunk.metadata.get("role") != "python_backend" for chunk in chunks)


def test_secretary_resume_drives_secretary_job_search():
    text = "秘书学本科，掌握公文写作、会议纪要、档案管理、Word、Excel和WPS。"
    skills = extract_skills_from_text(text)
    role = infer_target_role({}, text, skills)
    keywords = build_search_keywords(role, skills)

    assert role == "秘书/行政助理"
    assert keywords[:3] == ["秘书/行政助理", "秘书", "行政助理"]
    assert "秘书" in role_title_terms(role, skills)
    assert "公文写作" in skills


@pytest.mark.asyncio
async def test_secretary_career_query_does_not_force_python():
    result = await CareerPlanningAgent._analyze_profile({
        "profile": {
            "major": "秘书学",
            "skills": ["公文写作", "会议纪要"],
            "projects": [],
        },
        "request_payload": {"preferred_target_role": "行政助理"},
    })
    assert "行政助理" in result["retrieval_query"]
    assert "FastAPI" not in result["retrieval_query"]
    assert "Python 后端工程师" not in result["retrieval_query"]


@pytest.mark.asyncio
async def test_secretary_assessment_uses_secretary_filter():
    class Retriever:
        last_source = "local_keyword"
        last_error = None
        last_results = []

        async def retrieve(self, query, *, top_k=None, filters=None):
            assert filters == {"role": ["secretary_studies", "general"]}
            return []

    agent = CareerAssessmentAgent(gateway=object(), retriever=Retriever())
    await agent._retrieve({
        "query": "秘书学 行政助理 公文写作阶段考核",
        "context": {},
        "mode": "generate",
    })
