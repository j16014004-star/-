"""LangGraph agent for questions raised under career execution tasks."""
from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai.career_question_prompt import SYSTEM_PROMPT, build_user_prompt
from app.ai.knowledge import KnowledgeChunk, SkillAssessmentKnowledgeRetriever
from app.ai.resume_optimization_agent import _parse_json_object
from app.ai.tencent_maas import TencentMaaSModelGateway
from app.core.config import settings
from app.schemas.career_plan import CareerQuestionAIOutput


class CareerQuestionAgentState(TypedDict, total=False):
    question: str
    task_context: dict[str, Any]
    plan_context: dict[str, Any]
    sensitive_redacted: bool
    retrieval_query: str
    knowledge_chunks: list[KnowledgeChunk]
    retrieval_source: str
    retrieval_error: str | None
    retrieved_chunk_ids: list[str]
    retrieval_audit: list[dict]
    raw_output: str
    token_usage: dict[str, int]
    result: CareerQuestionAIOutput


class CareerQuestionAgent:
    def __init__(
        self,
        *,
        gateway: TencentMaaSModelGateway | None = None,
        retriever: SkillAssessmentKnowledgeRetriever | None = None,
    ) -> None:
        self.gateway = gateway or TencentMaaSModelGateway()
        self.retriever = retriever or SkillAssessmentKnowledgeRetriever(self.gateway)
        graph = StateGraph(CareerQuestionAgentState)
        graph.add_node("prepare", self._prepare)
        graph.add_node("retrieve_knowledge", self._retrieve_knowledge)
        graph.add_node("answer", self._answer)
        graph.add_node("validate", self._validate)
        graph.add_edge(START, "prepare")
        graph.add_edge("prepare", "retrieve_knowledge")
        graph.add_edge("retrieve_knowledge", "answer")
        graph.add_edge("answer", "validate")
        graph.add_edge("validate", END)
        self.graph = graph.compile()

    async def run(
        self,
        *,
        question: str,
        task_context: dict,
        plan_context: dict,
        sensitive_redacted: bool = False,
    ) -> CareerQuestionAgentState:
        return await self.graph.ainvoke({
            "question": question,
            "task_context": task_context,
            "plan_context": plan_context,
            "sensitive_redacted": sensitive_redacted,
        })

    @staticmethod
    async def _prepare(state: CareerQuestionAgentState) -> dict[str, str]:
        task = state.get("task_context") or {}
        plan = state.get("plan_context") or {}
        roles = " ".join(
            str(item.get("role_name") or "")
            for item in plan.get("recommended_roles") or []
            if isinstance(item, dict)
        )
        return {
            "retrieval_query": " ".join([
                state["question"],
                str(task.get("title") or ""),
                str(task.get("description") or ""),
                str(task.get("stage") or ""),
                roles,
            ])
        }

    async def _retrieve_knowledge(
        self, state: CareerQuestionAgentState
    ) -> dict[str, Any]:
        chunks = await self.retriever.retrieve(state["retrieval_query"])
        return {
            "knowledge_chunks": chunks,
            "retrieval_source": getattr(self.retriever, "last_source", "unknown"),
            "retrieval_error": getattr(self.retriever, "last_error", None),
            "retrieved_chunk_ids": [chunk.id for chunk in chunks],
            "retrieval_audit": getattr(self.retriever, "last_results", []),
        }

    async def _answer(self, state: CareerQuestionAgentState) -> dict[str, Any]:
        response = await self.gateway.generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(
                question=state["question"],
                task_context=state.get("task_context") or {},
                plan_context=state.get("plan_context") or {},
                knowledge_chunks=state.get("knowledge_chunks") or [],
                sensitive_redacted=state.get("sensitive_redacted", False),
            ),
            model_name=settings.CAREER_PLANNING_MODEL,
            max_tokens=settings.CAREER_QUESTION_MAX_OUTPUT_TOKENS,
        )
        return {"raw_output": response.content, "token_usage": response.usage}

    @staticmethod
    async def _validate(state: CareerQuestionAgentState) -> dict[str, Any]:
        result = CareerQuestionAIOutput.model_validate(_parse_json_object(state["raw_output"]))
        return {"result": result}
