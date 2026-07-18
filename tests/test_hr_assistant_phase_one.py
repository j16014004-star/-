import pytest
from pydantic import ValidationError

from app.ai.hr_application_agent import HrApplicationAgent
from app.automations.job_58_apply import (
    classify_job_page,
    find_58_chat_entry,
    infer_message_sender_from_class,
    is_direct_58_job_url,
    is_58_webim_url,
    job_titles_match,
    page_matches_job,
)
from app.schemas.hr import HrWorkspaceCreateRequest


def test_only_direct_58_job_links_are_eligible():
    assert is_direct_58_job_url("https://legoclick.58.com/jump?target=abc") is True
    assert is_direct_58_job_url("https://xa.58.com/job/123456.shtml") is True
    assert is_direct_58_job_url("https://xa.58.com/quanzhizhaopin/") is False
    assert is_direct_58_job_url("https://example.com/job/123") is False
    assert is_direct_58_job_url(None) is False


def test_58_job_identity_prefers_stable_source_id_over_title_text():
    assert page_matches_job(
        expected_source_id="123456789",
        expected_title="python后端开发工程师",
        current_url="https://xa.58.com/job/123456789.shtml",
        page_html="<h1>Python开发</h1>",
        page_text="Python开发 爱霖科技",
    )
    assert not page_matches_job(
        expected_source_id="123456789",
        expected_title="GIS后端开发工程师",
        current_url="https://xa.58.com/job/987654321.shtml",
        page_html="<h1>厨师</h1>",
        page_text="厨师 餐饮公司",
    )
    assert not page_matches_job(
        expected_source_id="123456789",
        expected_title="Python后端开发工程师",
        current_url="https://xa.58.com/job/987654321.shtml",
        page_html="<h1>Python后端开发工程师</h1>",
        page_text="Python后端开发工程师 同名但不是原岗位",
    )


def test_58_job_page_status_and_title_fallback_are_recognized():
    assert classify_job_page("Python开发 已申请 微聊") == "already_applied"
    assert classify_job_page("该职位已关闭") == "closed"
    assert classify_job_page("抱歉，该职位不存在，信息已删除") == "closed"
    assert classify_job_page("Python开发 立即申请") == "available"
    assert job_titles_match("Python后端开发工程师", "Python后端开发工程师 招聘详情")


def test_real_58_webim_url_is_recognized():
    assert is_58_webim_url("https://webim.58.com/indexNew?p=rb&_=123")
    assert not is_58_webim_url("https://xa.58.com/job/123456.shtml")
    assert not is_58_webim_url("https://example.com/webim")


def test_ambiguous_58_message_class_is_not_assumed_to_be_hr():
    assert infer_message_sender_from_class("im-msg") is None
    assert infer_message_sender_from_class("im-msg im-msg-me") is None
    assert infer_message_sender_from_class("im-msg incoming left") == "hr"
    assert infer_message_sender_from_class("im-msg outgoing right") == "user"


@pytest.mark.asyncio
async def test_58_chat_entry_prefers_clickable_parent(monkeypatch):
    clickable_parent = object()
    seen = []

    async def fake_selector(page, selector):
        seen.append(selector)
        return clickable_parent

    async def text_lookup_must_not_run(page, label):
        raise AssertionError("text child fallback must not run when .bangbangBtn exists")

    monkeypatch.setattr(
        "app.automations.job_58_apply.first_visible_selector", fake_selector
    )
    monkeypatch.setattr(
        "app.automations.job_58_apply.first_visible_text", text_lookup_must_not_run
    )

    assert await find_58_chat_entry(object()) is clickable_parent
    assert ".bangbangBtn" in seen[0]


def test_optimized_resume_requires_saved_version_id():
    with pytest.raises(ValidationError):
        HrWorkspaceCreateRequest(
            job_id=1, resume_id=2, resume_source="optimized",
            automation_mode="assisted", manual_login_confirmed=True,
        )


def test_full_auto_workspace_request_is_supported():
    value = HrWorkspaceCreateRequest(
        job_id=1,
        resume_id=2,
        resume_source="original",
        automation_mode="full_auto",
        manual_login_confirmed=True,
    )
    assert value.automation_mode == "full_auto"
    assert value.permissions.auto_apply is True


@pytest.mark.asyncio
async def test_hr_agent_validates_json_and_reports_used_fallback_model():
    class Response:
        content = '{"content":"您好，我具备岗位要求的Python和FastAPI技能，希望进一步沟通。","reason":"简历技能与岗位要求匹配"}'
        usage = {"prompt_tokens": 30, "completion_tokens": 20, "total_tokens": 50}
        model_name = "glm-5.1"

    class Gateway:
        async def generate_json(self, **kwargs):
            assert "不得虚构" in kwargs["system_prompt"]
            return Response()

    state = await HrApplicationAgent(gateway=Gateway()).run(
        job={"title": "Python后端工程师", "skills": ["Python", "FastAPI"]},
        resume_text="技能：Python、FastAPI",
    )
    assert state["result"].content.startswith("您好")
    assert state["used_model_name"] == "glm-5.1"
    assert state["token_usage"]["total_tokens"] == 50


def test_hr_routes_are_registered():
    from app.main import app
    paths = set(app.openapi()["paths"])
    assert "/api/hr/automation/preflight" in paths
    assert "/api/hr/workspaces" in paths
    assert "/api/hr/workspaces/{workspace_id}/actions/{action_id}/confirm" in paths
