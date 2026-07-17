"""LangGraph agent for stage assessment generation and subjective scoring."""
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai.knowledge import (
    SkillAssessmentKnowledgeRetriever,
    infer_knowledge_role,
    role_knowledge_filters,
)
from app.ai.resume_optimization_agent import _parse_json_object
from app.ai.tencent_maas import TencentMaaSModelGateway
from app.core.config import settings
from app.schemas.career_plan import CareerAssessmentEvaluationOutput, CareerAssessmentGenerationOutput


class AssessmentState(TypedDict, total=False):
    mode: str
    context: dict[str, Any]
    query: str
    knowledge_chunks: list
    raw_output: str
    token_usage: dict
    used_model_name: str | None
    retrieval_source: str
    retrieval_error: str | None
    retrieval_audit: list[dict]
    result: Any


class CareerAssessmentAgent:
    def __init__(self, gateway=None, retriever=None):
        self.gateway = gateway or TencentMaaSModelGateway()
        self.retriever = retriever or SkillAssessmentKnowledgeRetriever(self.gateway)
        graph = StateGraph(AssessmentState)
        graph.add_node("retrieve", self._retrieve)
        graph.add_node("generate", self._generate)
        graph.add_node("validate", self._validate)
        graph.add_edge(START, "retrieve")
        graph.add_edge("retrieve", "generate")
        graph.add_edge("generate", "validate")
        graph.add_edge("validate", END)
        self.graph = graph.compile()

    async def run(self, *, mode: str, context: dict) -> AssessmentState:
        return await self.graph.ainvoke({"mode": mode, "context": context, "query": str(context)[:4000]})

    async def _retrieve(self, state):
        chunks = await self.retriever.retrieve(
            state["query"], filters=role_knowledge_filters(state["query"])
        )
        return {
            "knowledge_chunks": chunks,
            "retrieval_source": getattr(self.retriever, "last_source", "unknown"),
            "retrieval_error": getattr(self.retriever, "last_error", None),
            "retrieval_audit": getattr(self.retriever, "last_results", []),
        }

    async def _generate(self, state):
        chunks = "\n".join(f"- {item.content}" for item in state.get("knowledge_chunks") or [])
        role = infer_knowledge_role(state.get("query"), state.get("context"))
        if state["mode"] == "generate":
            question_types = (
                "覆盖选择题(choice)、多选题(multiple)和基于办公情境的简答题(short)，"
                "秘书学方向禁止生成代码题(code)。"
                if role == "secretary_studies"
                else "覆盖选择题(choice)、多选题(multiple)、简答题(short)和代码分析题(code)。"
            )
            instruction = (
                f"生成6到10道与当前目标岗位一致的阶段考核题，{question_types}"
                "总分尽量为100。客观题必须给correct_answer，主观题必须给reference_answer和rubric。"
                "禁止要求或输出密码、Token、API Key等敏感信息。只返回符合CareerAssessmentGenerationOutput的JSON。"
            )
        else:
            instruction = (
                "只评阅short/code主观答案，不执行任何代码。严格按题目points与rubric评分，返回每题question_id、score(0到该题满分)、rationale，"
                "并给summary、strengths、weaknesses、improvement_advice。只返回符合CareerAssessmentEvaluationOutput的JSON。"
            )
        response = await self.gateway.generate_json(
            system_prompt="你是严谨的职业技能阶段考核专家。所有结论必须有评分依据。",
            user_prompt=f"{instruction}\n上下文：{state['context']}\n参考知识：{chunks}",
            model_name=settings.CAREER_PLANNING_MODEL,
            max_tokens=3000,
        )
        return {
            "raw_output": response.content,
            "token_usage": response.usage,
            "used_model_name": response.model_name,
        }

    async def _validate(self, state):
        model = CareerAssessmentGenerationOutput if state["mode"] == "generate" else CareerAssessmentEvaluationOutput
        return {"result": model.model_validate(_parse_json_object(state["raw_output"]))}
