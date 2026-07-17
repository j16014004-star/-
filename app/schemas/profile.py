from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=2, max_length=50)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=6, max_length=64)
    new_password: str = Field(min_length=8, max_length=64)


class TwoFactorSetup(BaseModel):
    password: str = Field(min_length=6, max_length=64)


class TwoFactorEnable(BaseModel):
    code: str = Field(min_length=6, max_length=12)


class TwoFactorDisable(BaseModel):
    password: str = Field(min_length=6, max_length=64)
    code: str = Field(min_length=6, max_length=12)


class PreferenceUpdate(BaseModel):
    email_notifications: bool | None = None
    push_notifications: bool | None = None
    ai_report_notifications: bool | None = None

    @model_validator(mode="after")
    def require_value(self):
        if not self.model_fields_set:
            raise ValueError("至少提交一个偏好设置")
        return self


class AccountDelete(BaseModel):
    password: str = Field(min_length=6, max_length=64)
    confirmation: Literal["确认删除"]
    code: str | None = Field(default=None, min_length=6, max_length=12)
