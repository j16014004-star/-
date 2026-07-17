"""LangGraph interview invitation detector; it never confirms an interview."""
from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai.hr_interview_prompt import SYSTEM_PROMPT, build_user_prompt
from app.ai.resume_optimization_agent import _parse_json_object
from app.ai.tencent_maas import TencentMaaSModelGateway
from app.core.config import settings
from app.schemas.hr import HrInterviewDetectionAIOutput


class HrInterviewState(TypedDict, total=False):
    current_time: str
    message: str
    job: dict[str, Any]
    raw_output: str
    token_usage: dict[str, int]
    used_model_name: str | None
    result: HrInterviewDetectionAIOutput


class HrInterviewAgent:
    def __init__(self, gateway: TencentMaaSModelGateway | None = None) -> None:
        self.gateway = gateway or TencentMaaSModelGateway()
        graph = StateGraph(HrInterviewState)
        graph.add_node("extract", self._extract)
        graph.add_node("validate", self._validate)
        graph.add_edge(START, "extract")
        graph.add_edge("extract", "validate")
        graph.add_edge("validate", END)
        self.graph = graph.compile()

    async def run(self, *, current_time: str, message: str, job: dict) -> HrInterviewState:
        return await self.graph.ainvoke(
            {"current_time": current_time, "message": message, "job": job}
        )

    async def _extract(self, state: HrInterviewState) -> dict[str, Any]:
        response = await self.gateway.generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(
                current_time=state["current_time"], message=state["message"], job=state["job"]
            ),
            model_name=settings.HR_ASSISTANT_MODEL,
            max_tokens=settings.HR_APPLICATION_MAX_OUTPUT_TOKENS,
        )
        return {"raw_output": response.content, "token_usage": response.usage,
                "used_model_name": response.model_name}

    @staticmethod
    async def _validate(state: HrInterviewState) -> dict[str, Any]:
        return {"result": HrInterviewDetectionAIOutput.model_validate(
            _parse_json_object(state["raw_output"])
        )}
