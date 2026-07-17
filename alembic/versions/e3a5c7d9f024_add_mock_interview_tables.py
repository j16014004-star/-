"""add AI mock interview tables

Revision ID: e3a5c7d9f024
Revises: d2f4a6b8c013
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3a5c7d9f024"
down_revision: Union[str, None] = "d2f4a6b8c013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_table(name: str, *columns, **kwargs) -> None:
    """Support databases where FastAPI create_all created a table before Alembic ran."""
    if name not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table(name, *columns, **kwargs)


def _create_index(name: str, table_name: str, columns: list[str]) -> None:
    indexes = {item["name"] for item in sa.inspect(op.get_bind()).get_indexes(table_name)}
    if name not in indexes:
        op.create_index(name, table_name, columns)


def upgrade() -> None:
    _create_table(
        "mock_interviews",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("job_id", sa.BigInteger(), sa.ForeignKey("jobs.id", ondelete="SET NULL")),
        sa.Column("resume_id", sa.BigInteger(), sa.ForeignKey("resumes.id", ondelete="SET NULL")),
        sa.Column("resume_source", sa.String(20), nullable=False, server_default="original"),
        sa.Column("resume_optimization_id", sa.BigInteger(), sa.ForeignKey("resume_optimization_versions.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("target_role", sa.String(150), nullable=False),
        sa.Column("company", sa.String(200)),
        sa.Column("job_description", sa.Text()),
        sa.Column("domain", sa.String(30), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("question_types", sa.JSON(), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("current_question_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("overall_score", sa.Integer()),
        sa.Column("retrieval_source", sa.String(50)),
        sa.Column("retrieval_error", sa.String(500)),
        sa.Column("retrieval_audit", sa.JSON()),
        sa.Column("model_name", sa.String(100)),
        sa.Column("token_usage", sa.JSON()),
        sa.Column("prompt_version", sa.String(50), nullable=False),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    _create_index("ix_mock_interviews_user_id", "mock_interviews", ["user_id"])
    _create_index("ix_mock_interviews_status", "mock_interviews", ["status"])
    _create_table(
        "mock_interview_questions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("interview_id", sa.BigInteger(), sa.ForeignKey("mock_interviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_no", sa.Integer(), nullable=False),
        sa.Column("question_type", sa.String(30), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("intent", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("reference_points", sa.JSON(), nullable=False),
        sa.Column("rubric", sa.JSON(), nullable=False),
        sa.Column("knowledge_chunk_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("interview_id", "order_no", name="uq_mock_question_order"),
    )
    _create_index("ix_mock_interview_questions_interview_id", "mock_interview_questions", ["interview_id"])
    _create_table(
        "mock_interview_answers",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("question_id", sa.BigInteger(), sa.ForeignKey("mock_interview_questions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("dimension_scores", sa.JSON(), nullable=False),
        sa.Column("matched_points", sa.JSON(), nullable=False),
        sa.Column("missing_points", sa.JSON(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("follow_up_question", sa.Text()),
        sa.Column("model_name", sa.String(100)),
        sa.Column("token_usage", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    _create_index("ix_mock_interview_answers_user_id", "mock_interview_answers", ["user_id"])
    _create_table(
        "mock_interview_reports",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("interview_id", sa.BigInteger(), sa.ForeignKey("mock_interviews.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("dimension_scores", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=False),
        sa.Column("improvement_plan_7_days", sa.JSON(), nullable=False),
        sa.Column("improvement_plan_30_days", sa.JSON(), nullable=False),
        sa.Column("model_name", sa.String(100)),
        sa.Column("token_usage", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    _create_table(
        "mock_interview_question_recommendations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("interview_id", sa.BigInteger(), sa.ForeignKey("mock_interviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("weakness", sa.String(200), nullable=False),
        sa.Column("question_type", sa.String(30), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("reference_points", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    _create_index("ix_mock_recommendations_interview_id", "mock_interview_question_recommendations", ["interview_id"])


def downgrade() -> None:
    op.drop_table("mock_interview_question_recommendations")
    op.drop_table("mock_interview_reports")
    op.drop_table("mock_interview_answers")
    op.drop_table("mock_interview_questions")
    op.drop_table("mock_interviews")
