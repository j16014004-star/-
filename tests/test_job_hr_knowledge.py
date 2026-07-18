import pytest

from app.ai.hr_reply_agent import HrReplyAgent
from app.ai.knowledge import (
    HrCommunicationKnowledgeRetriever,
    JobRecommendationKnowledgeRetriever,
    KnowledgeChunk,
)
from app.automations.job_58_apply import is_58_webim_url
from app.automations.job_58_apply import (
    PlatformNetworkDenied,
    create_58_browser_context,
    close_58_browser_context,
    goto_58_page,
    is_network_access_denied,
    platform_error_message,
)
from playwright.async_api import Error as PlaywrightError
from app.services.job_recommendation_rules import (
    expand_search_keywords_from_knowledge,
    score_job_match,
)


@pytest.mark.asyncio
async def test_new_knowledge_bases_are_retrievable_locally(monkeypatch):
    monkeypatch.setattr("app.ai.knowledge.settings.QDRANT_ENABLED", False)
    job = await JobRecommendationKnowledgeRetriever().retrieve(
        "Python后端开发工程师 FastAPI 岗位匹配", top_k=2
    )
    hr = await HrCommunicationKnowledgeRetriever().retrieve(
        "HR询问到岗时间和期望薪资", top_k=2
    )
    assert job and any("岗位" in chunk.content for chunk in job)
    assert hr and any("确认" in chunk.content for chunk in hr)


def test_job_kb_expands_only_selected_role_aliases_and_explains_score():
    chunk = KnowledgeChunk(
        id="1",
        document_id="doc",
        title="岗位规范",
        section="技术岗位别名",
        content=(
            "Python后端开发工程师：Python后端开发、Python开发工程师、后端开发工程师。\n"
            "Java后端开发工程师：Java开发工程师、Java后端开发。"
        ),
        source_file="岗位规范.md",
        version="v1",
    )
    keywords = expand_search_keywords_from_knowledge(
        "Python后端开发工程师", ["Python后端开发工程师"], [chunk]
    )
    assert "Python开发工程师" in keywords
    assert "Java开发工程师" not in keywords

    score, _, reasons, relevant = score_job_match(
        target_role="Python后端开发工程师",
        target_city="西安",
        resume_skills=["Python", "FastAPI"],
        job_title="Python后端开发工程师",
        job_city="西安",
        job_skills=["Python"],
        job_description="FastAPI接口开发",
        knowledge_context=chunk.content,
    )
    assert relevant is True
    assert score > 0
    assert "岗位方向符合推荐知识库规范" in reasons


@pytest.mark.asyncio
async def test_hr_reply_agent_retrieves_policy_before_generation():
    class Retriever:
        last_source = "qdrant_vector"
        last_error = None
        last_results = [{"chunk_id": "hr-1", "source_file": "HR规范.md"}]

        async def retrieve(self, query, *, top_k=None, filters=None):
            assert "到岗" in query
            return [
                KnowledgeChunk(
                    id="hr-1",
                    document_id="doc",
                    title="HR规范",
                    section="到岗时间",
                    content="未确认到岗时间时必须让用户确认。",
                    source_file="HR规范.md",
                    version="v1",
                )
            ]

    class Response:
        content = '{"items":[{"content":"到岗时间我确认后回复您。","reason":"依据沟通安全规范"}]}'
        usage = {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30}
        model_name = "glm-5"

    class Gateway:
        async def generate_json(self, **kwargs):
            assert "未确认到岗时间" in kwargs["user_prompt"]
            return Response()

    state = await HrReplyAgent(gateway=Gateway(), retriever=Retriever()).run(
        job={"title": "Python后端开发工程师"},
        resume_text="掌握Python",
        messages=[{"sender_type": "hr", "content": "什么时候可以到岗？"}],
    )
    assert state["retrieval_source"] == "qdrant_vector"
    assert state["result"].items[0].content


def test_only_real_58_webim_urls_are_accepted():
    assert is_58_webim_url("https://webim.58.com/indexNew") is True
    assert is_58_webim_url("https://example.com/indexNew") is False


def test_network_denied_error_is_classified_with_nonempty_detail():
    error = PlaywrightError("Page.goto: net::ERR_NETWORK_ACCESS_DENIED")
    assert is_network_access_denied(error) is True
    assert "ERR_NETWORK_ACCESS_DENIED" in platform_error_message(error)
    assert platform_error_message(TimeoutError()) == "TimeoutError: 未提供详细错误"


@pytest.mark.asyncio
async def test_goto_converts_network_denied_to_platform_error():
    class Page:
        async def goto(self, *args, **kwargs):
            raise PlaywrightError("net::ERR_NETWORK_ACCESS_DENIED")

    with pytest.raises(PlatformNetworkDenied, match="无法访问58同城"):
        await goto_58_page(Page(), "https://xa.58.com/job")


@pytest.mark.asyncio
async def test_hr_browser_uses_configured_remote_cdp(monkeypatch, tmp_path):
    state = tmp_path / "58.json"
    state.write_text('{"cookies":[],"origins":[]}', encoding="utf-8")

    class Browser:
        async def new_context(self, **kwargs):
            assert kwargs["storage_state"]["cookies"] == []
            return object()

    class Chromium:
        async def connect_over_cdp(self, endpoint):
            assert endpoint == "http://browser:9222"
            return Browser()

        async def launch(self, **kwargs):
            raise AssertionError("configured CDP must be preferred")

    class Playwright:
        chromium = Chromium()

    monkeypatch.setattr(
        "app.automations.job_58_apply.settings.PLAYWRIGHT_CDP_ENDPOINT",
        "http://browser:9222",
    )
    browser, context = await create_58_browser_context(Playwright(), str(state))
    assert isinstance(browser, Browser)
    assert context is not None


@pytest.mark.asyncio
async def test_closing_remote_context_does_not_close_shared_browser(monkeypatch):
    calls = []

    class Browser:
        async def close(self):
            calls.append("browser")

    class Context:
        async def close(self):
            calls.append("context")

    monkeypatch.setattr(
        "app.automations.job_58_apply.settings.PLAYWRIGHT_CDP_ENDPOINT",
        "http://browser:9222",
    )
    await close_58_browser_context(Browser(), Context())
    assert calls == ["context"]
