from app.services.job_recommendation_rules import (
    build_search_keywords,
    infer_target_city,
    infer_target_role,
    score_job_match,
)
from app.services.platform_session_service import is_plausible_storage_state


def test_search_intent_uses_role_terms_instead_of_long_resume_skills():
    skills = ["面向对象编程", "FastAPI", "SQLAlchemyAsyncORM", "RESTfulAPI开发"]
    role = infer_target_role({}, "", skills)
    keywords = build_search_keywords(role, skills)

    assert role == "Python后端开发工程师"
    assert keywords == ["Python后端开发工程师", "Python后端开发", "Python开发工程师", "后端开发工程师"]
    assert "SQLAlchemyAsyncORM" not in keywords

    # 用户明确选择岗位时必须优先于简历中的技术技能。
    assert build_search_keywords("厨师", skills) == ["厨师", "中餐厨师", "餐饮厨师"]


def test_explicit_city_wins_and_resume_city_can_be_inferred():
    assert infer_target_city({"city": "深圳市"}, "") == "深圳"
    assert infer_target_city({}, "期望城市：杭州\n期望岗位：Python后端") == "杭州"


def test_matching_filters_unrelated_fallback_job_and_scores_relevant_job():
    common = {
        "target_role": "Python后端开发工程师",
        "target_city": "北京",
        "resume_skills": ["Python", "FastAPI", "MySQL"],
    }
    score, matched, reasons, relevant = score_job_match(
        **common,
        job_title="Python后端开发工程师",
        job_city="北京",
        job_skills=["Python", "FastAPI", "MySQL"],
        job_description="负责FastAPI服务和MySQL数据库开发",
    )
    assert relevant is True
    assert score >= 90
    assert matched == ["Python", "FastAPI", "MySQL"]
    assert any("岗位方向匹配" in reason for reason in reasons)

    score, _, reasons, relevant = score_job_match(
        **common,
        job_title="办公室文员",
        job_city="北京",
        job_skills=["Excel"],
        job_description="负责资料整理",
    )
    assert relevant is False
    assert score == 0
    assert reasons == ["岗位方向与目标岗位不一致"]


def test_saved_login_state_requires_unexpired_58_auth_cookie(tmp_path):
    state = tmp_path / "58.json"
    state.write_text(
        '{"cookies":[{"name":"id58","domain":".58.com","expires":4102444800}]}',
        encoding="utf-8",
    )
    assert is_plausible_storage_state(state, "58") is True

    state.write_text(
        '{"cookies":[{"name":"analytics","domain":".58.com","expires":4102444800}]}',
        encoding="utf-8",
    )
    assert is_plausible_storage_state(state, "58") is False
