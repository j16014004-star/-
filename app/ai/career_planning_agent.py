"""LangGraph career planning agent with career knowledge RAG."""
from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai.career_planning_prompt import SYSTEM_PROMPT, build_user_prompt
from app.ai.knowledge import (
    CareerKnowledgeRetriever,
    KnowledgeChunk,
    infer_knowledge_role,
    role_knowledge_filters,
)
from app.ai.resume_optimization_agent import _parse_json_object
from app.ai.tencent_maas import TencentMaaSModelGateway
from app.core.config import settings
from app.schemas.career_plan import CareerPlanAIOutput


class CareerPlanningAgentState(TypedDict, total=False):
    profile: dict[str, Any]
    project_attachments: list[dict[str, Any]]
    request_payload: dict[str, Any]
    max_output_tokens: int | None
    retrieval_query: str
    knowledge_chunks: list[KnowledgeChunk]
    retrieval_source: str
    retrieval_error: str | None
    retrieved_chunk_ids: list[str]
    retrieval_audit: list[dict]
    raw_output: str
    token_usage: dict[str, int]
    used_model_name: str | None
    result: CareerPlanAIOutput


class CareerPlanningAgent:
    def __init__(
        self,
        *,
        gateway: TencentMaaSModelGateway | None = None,
        retriever: CareerKnowledgeRetriever | None = None,
    ) -> None:
        self.gateway = gateway or TencentMaaSModelGateway()
        self.retriever = retriever or CareerKnowledgeRetriever(self.gateway)
        graph = StateGraph(CareerPlanningAgentState)
        graph.add_node("analyze_profile", self._analyze_profile)
        graph.add_node("retrieve_knowledge", self._retrieve_knowledge)
        graph.add_node("generate", self._generate)
        graph.add_node("validate", self._validate)
        graph.add_edge(START, "analyze_profile")
        graph.add_edge("analyze_profile", "retrieve_knowledge")
        graph.add_edge("retrieve_knowledge", "generate")
        graph.add_edge("generate", "validate")
        graph.add_edge("validate", END)
        self.graph = graph.compile()

    async def run(
        self,
        *,
        profile: dict[str, Any],
        project_attachments: list[dict[str, Any]] | None,
        request_payload: dict[str, Any],
        max_output_tokens: int | None = None,
    ) -> CareerPlanningAgentState:
        return await self.graph.ainvoke({
            "profile": profile,
            "project_attachments": project_attachments or [],
            "request_payload": request_payload,
            "max_output_tokens": max_output_tokens,
        })

    @staticmethod
    async def _analyze_profile(state: CareerPlanningAgentState) -> dict[str, Any]:
        profile = state["profile"]
        request_payload = state.get("request_payload") or {}
        target_role = (
            request_payload.get("preferred_target_role")
            or profile.get("preferred_target_role")
        )
        if not target_role:
            role = infer_knowledge_role(
                profile.get("major"),
                profile.get("education"),
                profile.get("skills"),
                profile.get("work_experience"),
            )
            target_role = "秘书/行政助理" if role == "secretary_studies" else "Python 后端工程师"
        skills = " ".join(profile.get("skills") or [])
        projects = " ".join(
            f"{item.get('name', '')} {item.get('description', '')} {item.get('role', '')}"
            for item in profile.get("projects") or []
            if isinstance(item, dict)
        )
        feedback = str(request_payload.get("feedback") or "")
        focus_areas = " ".join(request_payload.get("focus_areas") or [])
        query = (
            f"{target_role} 职业规划 专业能力 岗位要求 职业发展 "
            f"求职 学习计划 技能差距 项目包装 {skills} {projects} {feedback} {focus_areas}"
        )
        return {"retrieval_query": query}

    async def _retrieve_knowledge(self, state: CareerPlanningAgentState) -> dict[str, Any]:
        chunks = await self.retriever.retrieve(
            state["retrieval_query"],
            filters=role_knowledge_filters(state["retrieval_query"]),
        )
        return {
            "knowledge_chunks": chunks,
            "retrieval_source": getattr(self.retriever, "last_source", "unknown"),
            "retrieval_error": getattr(self.retriever, "last_error", None),
            "retrieved_chunk_ids": [chunk.id for chunk in chunks],
            "retrieval_audit": getattr(self.retriever, "last_results", []),
        }

    async def _generate(self, state: CareerPlanningAgentState) -> dict[str, Any]:
        prompt = build_user_prompt(
            profile=state["profile"],
            project_attachments=state.get("project_attachments") or [],
            request_payload=state.get("request_payload") or {},
            knowledge_chunks=state.get("knowledge_chunks") or [],
        )
        response = await self.gateway.generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            model_name=settings.CAREER_PLANNING_MODEL,
            max_tokens=state.get("max_output_tokens"),
        )
        return {
            "raw_output": response.content,
            "token_usage": response.usage,
            "used_model_name": response.model_name,
        }

    @staticmethod
    async def _validate(state: CareerPlanningAgentState) -> dict[str, Any]:
        payload = _parse_json_object(state["raw_output"])
        result = CareerPlanAIOutput.model_validate(payload)
        return {"result": result}
