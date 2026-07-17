from app.main import app
from app.models.career_plan import CareerStageAssessmentQuestion
from app.services.career_assessment_service import _normalize_points, _objective_score
from app.ai.knowledge import SkillAssessmentKnowledgeRetriever, load_knowledge_chunks


def test_stage_assessment_routes_are_registered():
    paths = app.openapi()["paths"]
    expected = {
        "/api/career-plan-executions/{execution_plan_id}/advance",
        "/api/career-plan-executions/{execution_plan_id}/complete-all",
        "/api/career-plan-executions/{execution_plan_id}/assessments",
        "/api/career-plan-executions/assessments/{assessment_id}",
        "/api/career-plan-executions/assessments/{assessment_id}/submit",
        "/api/career-plan-executions/assessments/{assessment_id}/result",
        "/api/career-plan-executions/assessments/{assessment_id}/next-stage",
        "/api/career-plan-executions/assessments/{assessment_id}/remediation",
    }
    assert expected <= set(paths)


def test_question_points_are_normalized_to_exactly_one_hundred():
    points = _normalize_points([100, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    assert len(points) == 10
    assert all(item >= 1 for item in points)
    assert sum(points) == 100


def test_objective_scoring_is_rule_based_and_order_independent_for_multiple():
    multiple = CareerStageAssessmentQuestion(
        question_type="multiple", correct_answer=["A", "C"], points=15
    )
    choice = CareerStageAssessmentQuestion(
        question_type="choice", correct_answer="B", points=10
    )
    assert _objective_score(multiple, ["C", "A"]) == 15
    assert _objective_score(multiple, ["A"]) == 0
    assert _objective_score(choice, "B") == 10
    assert _objective_score(choice, "A") == 0


def test_code_answer_is_never_rule_executed():
    question = CareerStageAssessmentQuestion(
        question_type="code", correct_answer=None, points=20
    )
    assert _objective_score(question, "import os; os.remove('anything')") is None


def test_skill_assessment_knowledge_has_rubrics_and_security_rules():
    chunks = load_knowledge_chunks("knowledge_base/skill_assessment/source")
    assert len(chunks) >= 10
    combined = "\n".join(f"{item.section}\n{item.content}" for item in chunks)
    assert "代码题永远只做静态文本分析" in combined
    assert "阶段考核组卷规则" in combined
    assert any(item.metadata.get("knowledge_type") == "rubric" for item in chunks)


def test_skill_assessment_local_metadata_filter(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.QDRANT_ENABLED", False)
    retriever = SkillAssessmentKnowledgeRetriever()
    chunks = retriever._retrieve_local(
        "FastAPI 权限测试", 3, {"role": "python_backend"}
    )
    assert chunks
    assert all(item.metadata["role"] == "python_backend" for item in chunks)
    assert retriever.collection_name == "career_skill_assessment_kb"
