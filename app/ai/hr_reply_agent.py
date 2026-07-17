"""LangGraph agent for HR reply suggestions; it never sends messages."""
from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai.knowledge import (
    HrCommunicationKnowledgeRetriever,
    KnowledgeChunk,
    role_knowledge_filters,
)
from app.ai.hr_reply_prompt import SYSTEM_PROMPT, build_user_prompt
from app.ai.resume_optimization_agent import _parse_json_object
from app.ai.tencent_maas import TencentMaaSModelGateway
from app.core.config import settings
from app.schemas.hr import HrReplySuggestionAIOutput


class HrReplyState(TypedDict, total=False):
    job: dict[str, Any]
    resume_text: str
    messages: list[dict[str, Any]]
    knowledge_chunks: list[KnowledgeChunk]
    retrieval_source: str
    retrieval_error: str | None
    retrieval_audit: list[dict]
    raw_output: str
    token_usage: dict[str, int]
    used_model_name: str | None
    result: HrReplySuggestionAIOutput


class HrReplyAgent:
    def __init__(
        self,
        gateway: TencentMaaSModelGateway | None = None,
        retriever: HrCommunicationKnowledgeRetriever | None = None,
    ) -> None:
        self.gateway = gateway or TencentMaaSModelGateway()
        self.retriever = retriever or HrCommunicationKnowledgeRetriever(self.gateway)
        graph = StateGraph(HrReplyState)
        graph.add_node("retrieve", self._retrieve)
        graph.add_node("generate", self._generate)
        graph.add_node("validate", self._validate)
        graph.add_edge(START, "retrieve")
        graph.add_edge("retrieve", "generate")
        graph.add_edge("generate", "validate")
        graph.add_edge("validate", END)
        self.graph = graph.compile()

    async def run(self, *, job: dict, resume_text: str, messages: list[dict]) -> HrReplyState:
        return await self.graph.ainvoke({"job": job, "resume_text": resume_text, "messages": messages})

    async def _retrieve(self, state: HrReplyState) -> dict[str, Any]:
        latest = " ".join(
            str(item.get("content") or "") for item in state.get("messages", [])[-6:]
        )
        job = state.get("job") or {}
        query = " ".join(
            filter(None, [
                str(job.get("title") or ""),
                state.get("resume_text", "")[:2000],
                latest,
            ])
        )[:4000]
        chunks = await self.retriever.retrieve(
            query,
            top_k=3,
            filters=role_knowledge_filters(query),
        )
        return {
            "knowledge_chunks": chunks,
            "retrieval_source": getattr(self.retriever, "last_source", "unknown"),
            "retrieval_error": getattr(self.retriever, "last_error", None),
            "retrieval_audit": getattr(self.retriever, "last_results", []),
        }

    async def _generate(self, state: HrReplyState) -> dict[str, Any]:
        response = await self.gateway.generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(
                job=state["job"],
                resume_text=state["resume_text"],
                messages=state["messages"],
                knowledge_chunks=state.get("knowledge_chunks") or [],
            ),
            model_name=settings.HR_ASSISTANT_MODEL,
            max_tokens=settings.HR_APPLICATION_MAX_OUTPUT_TOKENS,
        )
        return {"raw_output": response.content, "token_usage": response.usage,
                "used_model_name": response.model_name}

    @staticmethod
    async def _validate(state: HrReplyState) -> dict[str, Any]:
        return {"result": HrReplySuggestionAIOutput.model_validate(
            _parse_json_object(state["raw_output"])
        )}
