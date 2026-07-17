"""Schemas for AI mock interview APIs and agents."""
from typing import Literal

from pydantic import BaseModel, Field, model_validator


InterviewSource = Literal["applied", "intention", "custom"]
InterviewDomain = Literal["python_backend", "secretary_studies"]
InterviewDifficulty = Literal["junior", "middle", "senior"]
InterviewQuestionType = Literal["technical", "project", "behavioral", "scenario"]


class MockInterviewCreateRequest(BaseModel):
    source_type: InterviewSource
    job_id: int | None = Field(default=None, gt=0)
    resume_id: int | None = Field(default=None, gt=0)
    resume_source: Literal["original", "optimized"] = "original"
    resume_optimization_id: int | None = Field(default=None, gt=0)
    title: str | None = Field(default=None, max_length=200)
    target_role: str | None = Field(default=None, max_length=150)
    company: str | None = Field(default=None, max_length=200)
    job_description: str | None = Field(default=None, max_length=10000)
    difficulty: InterviewDifficulty = "middle"
    question_types: list[InterviewQuestionType] = Field(
        default_factory=lambda: ["technical", "project", "behavioral"], min_length=1, max_length=4
    )
    question_count: int = Field(default=6, ge=3, le=15)
    focus_weaknesses: list[str] = Field(default_factory=list, max_length=10, exclude=True)

    @model_validator(mode="after")
    def validate_source(self):
        if self.source_type == "applied" and not self.job_id:
            raise ValueError("已投递岗位面试必须选择岗位")
        if self.source_type in {"intention", "custom"} and not (self.target_role or "").strip():
            raise ValueError("意向岗位或自定义岗位必须填写目标岗位")
        if self.resume_source == "optimized" and not self.resume_optimization_id:
            raise ValueError("使用优化简历时必须选择优化简历版本")
        self.question_types = list(dict.fromkeys(self.question_types))
        for name in ("title", "target_role", "company", "job_description"):
            value = getattr(self, name)
            if value is not None:
                setattr(self, name, value.strip() or None)
        return self


class MockInterviewAnswerRequest(BaseModel):
    question_id: int = Field(gt=0)
    answer: str = Field(min_length=1, max_length=8000)
    duration_seconds: int = Field(default=0, ge=0, le=7200)

    @model_validator(mode="after")
    def normalize(self):
        self.answer = self.answer.strip()
        if not self.answer:
            raise ValueError("回答内容不能为空")
        return self


class GeneratedInterviewQuestion(BaseModel):
    question_type: InterviewQuestionType
    question: str = Field(min_length=5, max_length=1000)
    intent: str = Field(min_length=2, max_length=1000)
    difficulty: InterviewDifficulty
    reference_points: list[str] = Field(min_length=1, max_length=12)
    rubric: dict[str, int | str | list[str]]


class InterviewQuestionGenerationOutput(BaseModel):
    questions: list[GeneratedInterviewQuestion] = Field(min_length=3, max_length=15)


class InterviewAnswerEvaluationOutput(BaseModel):
    score: int = Field(ge=0, le=100)
    dimension_scores: dict[str, int]
    matched_points: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    feedback: str = Field(min_length=2, max_length=3000)
    follow_up_question: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_dimensions(self):
        self.dimension_scores = {
            str(key): max(0, min(100, int(value)))
            for key, value in self.dimension_scores.items()
        }
        return self


class InterviewQuestionBankItem(BaseModel):
    weakness: str = Field(min_length=1, max_length=200)
    question_type: InterviewQuestionType
    question: str = Field(min_length=5, max_length=1000)
    difficulty: InterviewDifficulty
    reference_points: list[str] = Field(min_length=1, max_length=12)


class InterviewReportGenerationOutput(BaseModel):
    summary: str = Field(min_length=10, max_length=3000)
    strengths: list[str] = Field(min_length=1, max_length=10)
    weaknesses: list[str] = Field(min_length=1, max_length=10)
    improvement_plan_7_days: list[str] = Field(min_length=1, max_length=10)
    improvement_plan_30_days: list[str] = Field(min_length=1, max_length=10)
    question_bank: list[InterviewQuestionBankItem] = Field(min_length=3, max_length=15)
