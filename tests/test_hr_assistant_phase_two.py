import pytest
from pydantic import ValidationError
from types import SimpleNamespace

from app.ai.hr_reply_agent import HrReplyAgent
from app.automations.job_58_apply import infer_message_sender_from_class
from app.schemas.hr import HrPermissions, HrWorkspaceModeRequest
from app.services.hr_service import (
    HrServiceError,
    message_requires_confirmation,
    platform_message_reference,
    process_workspace_automation,
    run_workspace_monitor_cycle,
)
from app.workers.hr_monitor_worker import interval_seconds, max_runtime_seconds


def test_manual_mode_must_disable_all_automation_permissions():
    with pytest.raises(ValidationError):
        HrWorkspaceModeRequest(
            automation_mode="manual",
            permissions=HrPermissions(auto_apply=True),
        )
    value = HrWorkspaceModeRequest(
        automation_mode="manual",
        permissions=HrPermissions(
            auto_apply=False, auto_greeting=False,
            auto_reply=False, auto_schedule_interview=False,
        ),
    )
    assert value.automation_mode == "manual"


def test_full_auto_mode_accepts_automation_permissions():
    value = HrWorkspaceModeRequest(
        automation_mode="full_auto",
        permissions=HrPermissions(
            auto_apply=True,
            auto_greeting=True,
            auto_reply=True,
            auto_schedule_interview=True,
        ),
    )
    assert value.automation_mode == "full_auto"


def test_hr_monitor_defaults_are_bounded(monkeypatch):
    monkeypatch.setenv("HR_MONITOR_INTERVAL_SECONDS", "1")
    monkeypatch.setenv("HR_MONITOR_MAX_SECONDS", "1")
    assert interval_seconds() == 15
    assert max_runtime_seconds() == 300


def test_sensitive_or_commitment_messages_require_second_confirmation():
    assert message_requires_confirmation("我的身份证号稍后发给您") is True
    assert message_requires_confirmation("验证码是123456") is True
    assert message_requires_confirmation("我现在支付押金并转账") is True
    assert message_requires_confirmation("我接受贵公司的Offer") is True
    assert message_requires_confirmation("我承诺接受这个薪资方案") is True
    assert message_requires_confirmation("我确认面试时间是周五下午") is True
    assert message_requires_confirmation("您好，我想进一步了解岗位职责") is False


def test_platform_message_id_is_preferred_and_fallback_uses_sender_content_time():
    assert platform_message_reference({
        "platform_message_id": "msg-100",
        "sender_type": "hr",
        "content": "您好",
        "message_time": "10:30",
    }) == "58:id:msg-100"
    first = platform_message_reference({
        "sender_type": "hr", "content": "请介绍项目", "message_time": "10:31",
    })
    same = platform_message_reference({
        "sender_type": "hr", "content": " 请介绍项目 ", "message_time": "10:31",
    })
    different_time = platform_message_reference({
        "sender_type": "hr", "content": "请介绍项目", "message_time": "10:32",
    })
    assert first == same
    assert first != different_time
    assert first.startswith("58:fallback:")


def test_platform_message_sender_must_be_unambiguous():
    assert infer_message_sender_from_class("message-item incoming left") == "hr"
    assert infer_message_sender_from_class("msg-item outgoing right") == "user"
    assert infer_message_sender_from_class("message-item") is None


@pytest.mark.asyncio
async def test_backend_queues_one_ai_reply_for_latest_unanswered_hr_message(monkeypatch):
    workspace = SimpleNamespace(
        id=3,
        user_id=9,
        automation_mode="full_auto",
        status="communicating",
        permissions={"auto_reply": True, "auto_schedule_interview": False},
    )
    monkeypatch.setattr(
        "app.services.hr_service.list_messages",
        lambda *args, **kwargs: _async_value([
            SimpleNamespace(id=18, sender_type="hr", content="请介绍项目经验"),
        ]),
    )
    monkeypatch.setattr(
        "app.services.hr_service.generate_reply_suggestions",
        lambda *args, **kwargs: _async_value({
            "items": [{"content": "您好，我在项目中使用过 FastAPI。"}],
        }),
    )
    monkeypatch.setattr(
        "app.services.hr_service.create_outgoing_message",
        lambda *args, **kwargs: _async_value({
            "action_id": 22, "waiting_confirmation": False,
        }),
    )

    result = await process_workspace_automation(object(), workspace=workspace)
    assert result == {"automation_action": "reply_queued", "action_id": 22}


@pytest.mark.asyncio
async def test_backend_does_not_reply_when_latest_message_is_outgoing(monkeypatch):
    workspace = SimpleNamespace(
        id=3,
        user_id=9,
        automation_mode="full_auto",
        status="communicating",
        permissions={"auto_reply": True, "auto_schedule_interview": False},
    )
    monkeypatch.setattr(
        "app.services.hr_service.list_messages",
        lambda *args, **kwargs: _async_value([
            SimpleNamespace(id=18, sender_type="hr"),
            SimpleNamespace(id=19, sender_type="user"),
        ]),
    )
    result = await process_workspace_automation(object(), workspace=workspace)
    assert result == {"automation_action": None}


@pytest.mark.asyncio
async def test_monitor_stops_immediately_after_login_expiry(monkeypatch):
    active = SimpleNamespace(
        id=3,
        user_id=9,
        automation_mode="full_auto",
        status="communicating",
        permissions={"auto_reply": True, "auto_schedule_interview": True},
    )
    paused = SimpleNamespace(**{**active.__dict__, "status": "paused"})
    calls = {"workspace": 0}

    async def get_workspace(*_args, **_kwargs):
        calls["workspace"] += 1
        return active if calls["workspace"] == 1 else paused

    async def sync(*_args, **_kwargs):
        raise HrServiceError("58同城登录状态不可用，请重新登录", 409)

    class SessionContext:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, *_args):
            return False

    monkeypatch.setattr("app.core.database.async_session", lambda: SessionContext())
    monkeypatch.setattr("app.services.hr_service.get_workspace", get_workspace)
    monkeypatch.setattr("app.services.hr_service.sync_workspace_messages", sync)

    assert await run_workspace_monitor_cycle(3) is False


async def _async_value(value):
    return value


@pytest.mark.asyncio
async def test_reply_agent_only_returns_validated_suggestions():
    class Response:
        content = '{"items":[{"content":"您好，我的项目中使用过FastAPI，方便进一步沟通岗位要求吗？","reason":"依据简历中的FastAPI项目经验"}]}'
        usage = {"prompt_tokens": 20, "completion_tokens": 15, "total_tokens": 35}
        model_name = "minimax-m2.7"

    class Gateway:
        async def generate_json(self, **kwargs):
            assert "不能代替确认" in kwargs["system_prompt"]
            return Response()

    state = await HrReplyAgent(gateway=Gateway()).run(
        job={"title": "Python后端工程师"},
        resume_text="项目使用 FastAPI",
        messages=[{"sender_type": "hr", "content": "介绍一下项目经验"}],
    )
    assert len(state["result"].items) == 1
    assert state["used_model_name"] == "minimax-m2.7"


def test_phase_two_routes_are_registered_with_expected_methods():
    from app.main import app
    paths = app.openapi()["paths"]
    assert "patch" in paths["/api/hr/workspaces/{workspace_id}/mode"]
    assert "post" in paths["/api/hr/workspaces/{workspace_id}/control"]
    assert set(paths["/api/hr/workspaces/{workspace_id}/messages"]) >= {"get", "post"}
    assert "post" in paths["/api/hr/workspaces/{workspace_id}/reply-suggestions"]
    assert "post" in paths["/api/hr/workspaces/{workspace_id}/messages/sync"]
