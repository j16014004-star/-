"""LangGraph agents for question generation, answer scoring and final reports."""
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai.knowledge import create_interview_knowledge_retriever
from app.ai.resume_optimization_agent import _parse_json_object
from app.ai.tencent_maas import TencentMaaSModelGateway
from app.core.config import settings
from app.schemas.mock_interview import (
    InterviewAnswerEvaluationOutput,
    InterviewQuestionGenerationOutput,
    InterviewReportGenerationOutput,
)


SYSTEM_PROMPT = """你是公平、严谨且贴近真实招聘场景的模拟面试考官。
知识库只提供专业标准，不能视为候选人的经历；简历和岗位描述中的事实也不能擅自补全。
不得询问密码、验证码、身份证号码、银行卡、API Key等敏感信息，不得按性别、年龄、婚育等无关特征评分。
所有输出必须是一个合法 JSON 对象，不要使用 Markdown 代码块。"""


class InterviewAgentState(TypedDict, total=False):
    mode: str
    domain: str
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


class MockInterviewAgent:
    """One explicit LangGraph workflow shared by the three interview phases."""

    def __init__(self, *, domain: str, gateway=None, retriever=None):
        self.gateway = gateway or TencentMaaSModelGateway()
        self.retriever = retriever or create_interview_knowledge_retriever(domain, self.gateway)
        graph = StateGraph(InterviewAgentState)
        graph.add_node("retrieve_knowledge", self._retrieve)
        graph.add_node("call_interviewer", self._generate)
        graph.add_node("validate_output", self._validate)
        graph.add_edge(START, "retrieve_knowledge")
        graph.add_edge("retrieve_knowledge", "call_interviewer")
        graph.add_edge("call_interviewer", "validate_output")
        graph.add_edge("validate_output", END)
        self.graph = graph.compile()

    async def run(self, *, mode: str, context: dict[str, Any]) -> InterviewAgentState:
        query = " ".join(
            str(context.get(key) or "")
            for key in ("target_role", "job_description", "question", "weaknesses")
        )[:5000]
        return await self.graph.ainvoke(
            {"mode": mode, "domain": context["domain"], "context": context, "query": query}
        )

    async def _retrieve(self, state: InterviewAgentState):
        chunks = await self.retriever.retrieve(state["query"], top_k=4)
        return {
            "knowledge_chunks": chunks,
            "retrieval_source": getattr(self.retriever, "last_source", "unknown"),
            "retrieval_error": getattr(self.retriever, "last_error", None),
            "retrieval_audit": getattr(self.retriever, "last_results", []),
        }

    async def _generate(self, state: InterviewAgentState):
        context = state["context"]
        knowledge = "\n\n".join(
            f"[{item.section}] {item.content}" for item in state.get("knowledge_chunks") or []
        )
        mode = state["mode"]
        if mode == "questions":
            instruction = f"""生成恰好 {context['question_count']} 道互不重复的模拟面试题。
只使用这些题型：{context['question_types']}；难度：{context['difficulty']}。
围绕目标岗位、岗位描述和简历中的已知内容，至少包含专业能力、项目或情境、行为沟通。
秘书学方向不得生成代码题。每题返回 question_type、question、intent、difficulty、
reference_points 和 rubric。rubric 应给出百分制评价依据。输出符合 InterviewQuestionGenerationOutput。"""
        elif mode == "evaluate":
            instruction = """评阅当前一道回答。严格按题目参考要点和评分规则给出0到100分。
dimension_scores 必须包含 professional、analysis、evidence、communication 四项百分制分数。
只依据候选人的实际回答，不因表达风格或无关个人特征扣分；未提及的内容记为缺失，不能脑补。
给出 matched_points、missing_points、可执行 feedback；必要时给 follow_up_question。
输出符合 InterviewAnswerEvaluationOutput。"""
        elif mode == "report":
            instruction = """根据本场所有题目、回答和逐题评分生成最终报告。
总结必须与逐题证据一致，给 strengths、weaknesses、7天计划、30天计划。
生成3到10道针对薄弱项的新题，禁止复制本场原题，每题提供 weakness、question_type、
question、difficulty、reference_points。输出符合 InterviewReportGenerationOutput。"""
        else:
            raise ValueError("未知模拟面试 Agent 模式")
        response = await self.gateway.generate_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=f"{instruction}\n\n业务上下文：{context}\n\n专业知识与评分标准：{knowledge}",
            model_name=settings.MOCK_INTERVIEW_MODEL,
            max_tokens=settings.MOCK_INTERVIEW_MAX_OUTPUT_TOKENS,
        )
        return {
            "raw_output": response.content,
            "token_usage": response.usage,
            "used_model_name": response.model_name,
        }

    async def _validate(self, state: InterviewAgentState):
        output_models = {
            "questions": InterviewQuestionGenerationOutput,
            "evaluate": InterviewAnswerEvaluationOutput,
            "report": InterviewReportGenerationOutput,
        }
        model = output_models[state["mode"]]
        result = model.model_validate(_parse_json_object(state["raw_output"]))
        if state["mode"] == "questions":
            expected = int(state["context"]["question_count"])
            if len(result.questions) != expected:
                raise ValueError(f"AI 出题数量不正确，期望 {expected}，实际 {len(result.questions)}")
        return {"result": result}
