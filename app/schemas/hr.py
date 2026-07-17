"""HR assistant phase-one API and AI schemas."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class HrPermissions(BaseModel):
    auto_apply: bool = True
    auto_greeting: bool = True
    auto_reply: bool = False
    auto_schedule_interview: bool = False


class HrWorkspaceCreateRequest(BaseModel):
    job_id: int = Field(gt=0)
    source: Literal["58"] = "58"
    resume_id: int = Field(gt=0)
    resume_source: Literal["original", "optimized"] = "original"
    resume_optimization_id: int | None = Field(default=None, gt=0)
    automation_mode: Literal["full_auto", "assisted", "manual"] = "assisted"
    permissions: HrPermissions = Field(default_factory=HrPermissions)
    manual_login_confirmed: bool

    @model_validator(mode="after")
    def validate_selection(self):
        if self.resume_source == "optimized" and self.resume_optimization_id is None:
            raise ValueError("选择优化简历时必须提交 resume_optimization_id")
        if self.resume_source == "original" and self.resume_optimization_id is not None:
            raise ValueError("原始简历不能提交 resume_optimization_id")
        return self


class HrActionConfirmRequest(BaseModel):
    approved: bool
    note: str | None = Field(default=None, max_length=500)


class HrApplicationDraftAIOutput(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    reason: str = Field(min_length=1, max_length=500)


class HrWorkspaceModeRequest(BaseModel):
    automation_mode: Literal["full_auto", "assisted", "manual"]
    permissions: HrPermissions

    @model_validator(mode="after")
    def manual_disables_automation(self):
        if self.automation_mode == "manual" and any(self.permissions.model_dump().values()):
            raise ValueError("manual 模式必须关闭全部自动化权限")
        return self


class HrWorkspaceControlRequest(BaseModel):
    action: Literal["pause", "resume", "take_over", "terminate"]


class HrMessageSendRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    send_mode: Literal["manual", "ai_suggestion"] = "manual"


class HrReplySuggestionAIItem(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    reason: str = Field(min_length=1, max_length=500)


class HrReplySuggestionAIOutput(BaseModel):
    items: list[HrReplySuggestionAIItem] = Field(min_length=1, max_length=3)


class HrInterviewDetectRequest(BaseModel):
    message_id: int | None = Field(default=None, gt=0)


class HrInterviewCreateRequest(BaseModel):
    scheduled_at: datetime
    end_at: datetime | None = None
    timezone: str = Field(default="Asia/Shanghai", max_length=50)
    interview_type: str = Field(min_length=1, max_length=50)
    location: str | None = Field(default=None, max_length=500)
    meeting_url: str | None = Field(default=None, max_length=500, pattern=r"^https://")
    contact_name: str | None = Field(default=None, max_length=100)
    reply_content: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.scheduled_at.tzinfo is None:
            raise ValueError("面试开始时间必须包含时区")
        if self.end_at is not None and self.end_at.tzinfo is None:
            raise ValueError("面试结束时间必须包含时区")
        if self.end_at is not None and self.end_at <= self.scheduled_at:
            raise ValueError("面试结束时间必须晚于开始时间")
        normalized_type = "".join(self.interview_type.lower().split())
        if (
            any(marker in normalized_type for marker in ("视频", "线上", "在线", "远程", "online"))
            and not self.meeting_url
        ):
            raise ValueError("线上或视频面试必须填写会议链接")
        if (
            any(marker in normalized_type for marker in ("现场", "线下", "到店", "面谈", "onsite"))
            and not self.location
        ):
            raise ValueError("线下或现场面试必须填写地点")
        return self


class HrInterviewDetectionAIOutput(BaseModel):
    has_interview_invitation: bool
    scheduled_at: str | None = None
    end_at: str | None = None
    timezone: str = "Asia/Shanghai"
    interview_type: str | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, max_length=500)
    meeting_url: str | None = Field(default=None, max_length=500)
    contact_name: str | None = Field(default=None, max_length=100)
    evidence: str | None = Field(default=None, max_length=1000)
    missing_fields: list[str] = Field(default_factory=list, max_length=10)
    suggested_reply: str | None = Field(default=None, max_length=1000)
