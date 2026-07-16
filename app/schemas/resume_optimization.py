'''Schemas for resume optimization requests, tasks and results.'''
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


OptimizationType = Literal['general', 'target_role']
OptimizationFocus = Literal['work_experience', 'project_experience', 'skills', 'ats', 'all']
OptimizationStyle = Literal['professional', 'technical', 'management', 'graduate']
AITaskStatus = Literal[
    'pending', 'preparing', 'generating', 'validating', 'saving',
    'success', 'failed', 'cancelled',
]


class ResumeOptimizationRequest(BaseModel):
    analysis_id: int | None = Field(default=None, gt=0)
    optimization_type: OptimizationType = 'general'
    target_role: str | None = Field(default=None, max_length=100)
    optimization_focus: list[OptimizationFocus] = Field(min_length=1, max_length=5)
    style: OptimizationStyle = 'professional'
    preserve_structure: bool = True

    @model_validator(mode='after')
    def validate_options(self):
        self.optimization_focus = list(dict.fromkeys(self.optimization_focus))
        if 'all' in self.optimization_focus and len(self.optimization_focus) > 1:
            raise ValueError('all 不能与其他优化重点同时使用')
        if self.target_role is not None:
            self.target_role = self.target_role.strip() or None
        if self.optimization_type == 'target_role' and not self.target_role:
            raise ValueError('针对目标岗位优化时必须填写目标岗位')
        if self.optimization_type == 'general':
            self.target_role = None
        return self


class ManualConfirmationItem(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    answer: str = Field(min_length=1, max_length=4000)


class ConfirmationAIApplyRequest(BaseModel):
    optimized_content: str = Field(min_length=1, max_length=50000)
    confirmation_questions: list[str] = Field(default_factory=list, max_length=30)
    confirmed_answers: list[ManualConfirmationItem] = Field(default_factory=list, max_length=30)
    feedback: str | None = Field(default=None, max_length=2000)

    @model_validator(mode='after')
    def validate_confirmed_answers(self):
        self.confirmation_questions = list(dict.fromkeys(
            question.strip() for question in self.confirmation_questions if question.strip()
        ))
        question_set = set(self.confirmation_questions)
        seen: set[str] = set()
        normalized_answers: list[ManualConfirmationItem] = []
        for item in self.confirmed_answers:
            question = item.question.strip()
            if question not in question_set:
                raise ValueError('confirmed_answers 中的问题必须存在于 confirmation_questions')
            if question in seen:
                raise ValueError('同一个确认问题不能重复提交答案')
            seen.add(question)
            normalized_answers.append(ManualConfirmationItem(
                question=question,
                answer=item.answer.strip(),
            ))
        self.confirmed_answers = normalized_answers
        if self.feedback is not None:
            self.feedback = self.feedback.strip() or None
        return self


class ConfirmationManualApplyRequest(BaseModel):
    optimized_content: str = Field(min_length=1, max_length=50000)
    confirmations: list[ManualConfirmationItem] = Field(min_length=1, max_length=30)


class ConfirmationDismissRequest(BaseModel):
    confirmation_questions: list[str] = Field(default_factory=list, max_length=30)


class ConfirmationAction(BaseModel):
    type: Literal['ai', 'manual', 'dismiss']
    title: str = Field(min_length=1, max_length=100)
    questions: list[str] = Field(default_factory=list, max_length=30)
    added_content: str | None = Field(default=None, max_length=10000)
    summary: str | None = Field(default=None, max_length=2000)
    feedback: str | None = Field(default=None, max_length=2000)
    created_at: str = Field(min_length=1, max_length=50)


class OptimizationSaveRequest(BaseModel):
    optimized_content: str = Field(min_length=1, max_length=50000)
    confirmation_actions: list[ConfirmationAction] = Field(default_factory=list, max_length=30)
    change_items: list[dict] | None = Field(default=None, max_length=50)
    confirmation_questions: list[str] | None = Field(default=None, max_length=30)


class AIStartTaskResponse(BaseModel):
    task_id: str
    status: AITaskStatus
    result_id: int | None = None
    poll_after_seconds: int = 2


class AITaskResponse(BaseModel):
    task_id: str
    task_type: Literal['resume_optimization']
    status: AITaskStatus
    progress: int = Field(ge=0, le=100)
    result_id: int | None = None
    error_message: str | None = None
    poll_after_seconds: int = 2


class ResumeChangeItem(BaseModel):
    model_config = ConfigDict(extra='forbid')

    section: str = Field(min_length=1, max_length=100)
    original: str = Field(min_length=1, max_length=4000)
    optimized: str = Field(min_length=1, max_length=4000)
    reason: str = Field(min_length=1, max_length=1000)
    evidence: str = Field(min_length=1, max_length=2000)
    evidence_source: Literal['original_resume', 'user_confirmation', 'knowledge_base'] = 'original_resume'
    requires_confirmation: bool = False


class ResumeOptimizationAIOutput(BaseModel):
    model_config = ConfigDict(extra='forbid')

    optimization_summary: str = Field(min_length=1, max_length=2000)
    optimized_content: str = Field(min_length=1, max_length=50000)
    score_improvement: int = Field(ge=0, le=100)
    change_items: list[ResumeChangeItem] = Field(default_factory=list, max_length=50)
    confirmation_questions: list[str] = Field(default_factory=list, max_length=30)


class ResumeOptimizationResultResponse(BaseModel):
    id: int
    optimization_summary: str
    original: str
    optimized: str
    optimized_content: str
    score_improvement: int | None
    change_items: list[ResumeChangeItem]
    confirmation_questions: list[str]
    created_at: datetime
