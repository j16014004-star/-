"""Prompt for extracting interview proposals from an HR message."""
from __future__ import annotations

import json


SYSTEM_PROMPT = """你是严格的面试邀请信息提取器，只能从给定的HR原文提取信息。
不得猜测日期、年份、时间、地点、会议链接、联系人或面试形式。相对日期只有在提供当前日期后才能换算；不确定就设为 null 并写入 missing_fields。scheduled_at/end_at 必须使用带时区的 ISO 8601（中国时间用 +08:00）。evidence 必须是HR原文中真实存在的短句。suggested_reply只能表达待用户确认的建议，不能替用户承诺时间。
只输出合法JSON：{"has_interview_invitation":true,"scheduled_at":null,"end_at":null,"timezone":"Asia/Shanghai","interview_type":null,"location":null,"meeting_url":null,"contact_name":null,"evidence":"原文证据","missing_fields":["scheduled_at"],"suggested_reply":"建议回复"}。"""


def build_user_prompt(*, current_time: str, message: str, job: dict) -> str:
    return (
        f"当前时间：{current_time}\n岗位：{json.dumps(job, ensure_ascii=False)}"
        f"\nHR原文：\n{message}"
    )
