from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.ai.hr_interview_agent import HrInterviewAgent
from app.schemas.hr import HrInterviewCreateRequest
from app.services.hr_service import (
    build_interview_confirmation_reply,
    parse_ai_interview_time,
    required_interview_fields_missing,
    to_utc_naive,
)


def test_interview_schedule_requires_explicit_timezone():
    with pytest.raises(ValidationError):
        HrInterviewCreateRequest(
            scheduled_at=datetime(2027, 1, 1, 14, 0),
            interview_type="视频面试",
            reply_content="已确认，可以参加",
        )
    request = HrInterviewCreateRequest(
        scheduled_at=datetime.now(timezone(timedelta(hours=8))) + timedelta(days=1),
        interview_type="视频面试",
        meeting_url="https://meeting.example.com/abc",
        reply_content="该时间可以参加，请确认会议链接",
    )
    assert request.scheduled_at.tzinfo is not None
    with pytest.raises(ValidationError, match="会议链接"):
        HrInterviewCreateRequest(
            scheduled_at=datetime.now(timezone(timedelta(hours=8))) + timedelta(days=1),
            interview_type="视频面试",
            reply_content="我可以参加",
        )
    with pytest.raises(ValidationError, match="地点"):
        HrInterviewCreateRequest(
            scheduled_at=datetime.now(timezone(timedelta(hours=8))) + timedelta(days=1),
            interview_type="线下面试",
            reply_content="我可以参加",
        )


def test_ai_interview_time_is_normalized_to_utc_naive():
    parsed = parse_ai_interview_time("2027-01-02T14:00:00+08:00")
    assert parsed == datetime(2027, 1, 2, 6, 0)
    with pytest.raises(Exception):
        to_utc_naive(datetime(2027, 1, 2, 14, 0))


def test_interview_proposal_requires_time_type_and_matching_destination():
    scheduled = datetime(2027, 1, 2, 6, 0)
    assert required_interview_fields_missing(
        scheduled_at=scheduled,
        interview_type="视频面试",
        location=None,
        meeting_url=None,
    ) == ["meeting_url"]
    assert required_interview_fields_missing(
        scheduled_at=scheduled,
        interview_type="线下面试",
        location=None,
        meeting_url=None,
    ) == ["location"]
    assert required_interview_fields_missing(
        scheduled_at=scheduled,
        interview_type="视频面试",
        location=None,
        meeting_url="https://meeting.example.com/abc",
    ) == []


def test_complete_interview_generates_fact_only_confirmation_draft():
    content = build_interview_confirmation_reply(
        scheduled_at=datetime(2027, 1, 2, 6, 0),
        timezone_name="Asia/Shanghai",
        interview_type="视频面试",
        location=None,
        meeting_url="https://meeting.example.com/abc",
    )
    assert "2027年01月02日 14:00" in content
    assert "视频面试" in content
    assert "https://meeting.example.com/abc" in content
    assert "请您确认" in content


@pytest.mark.asyncio
async def test_interview_agent_returns_schema_validated_detection():
    class Response:
        content = (
            '{"has_interview_invitation":true,'
            '"scheduled_at":"2027-01-02T14:00:00+08:00",'
            '"end_at":null,"timezone":"Asia/Shanghai",'
            '"interview_type":"视频面试","location":null,"meeting_url":null,'
            '"contact_name":null,"evidence":"邀请您参加视频面试",'
            '"missing_fields":[],"suggested_reply":"时间需要我确认后回复您"}'
        )
        usage = {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80}
        model_name = "glm-5"

    class Gateway:
        async def generate_json(self, **kwargs):
            assert "不得猜测日期" in kwargs["system_prompt"]
            return Response()

    state = await HrInterviewAgent(gateway=Gateway()).run(
        current_time="2026-12-30T10:00:00+08:00",
        message="邀请您参加视频面试，时间为1月2日下午2点",
        job={"title": "Python后端工程师"},
    )
    assert state["result"].has_interview_invitation is True
    assert state["used_model_name"] == "glm-5"


def test_phase_three_routes_are_registered():
    from app.main import app
    paths = app.openapi()["paths"]
    assert "post" in paths["/api/hr/workspaces/{workspace_id}/interviews/detect"]
    assert set(paths["/api/hr/workspaces/{workspace_id}/interviews"]) >= {"get", "post"}
    assert "get" in paths["/api/hr/interviews/upcoming"]
