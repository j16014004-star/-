"""add asynchronous career execution task questions

Revision ID: f9b3d5e7a012
Revises: e8a2c4d6f901
Create Date: 2026-07-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "f9b3d5e7a012"
down_revision: Union[str, Sequence[str], None] = "e8a2c4d6f901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if "career_plan_questions" in set(sa.inspect(op.get_bind()).get_table_names()):
        return
    op.create_table(
        "career_plan_questions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("execution_task_id", sa.BigInteger(), nullable=False),
        sa.Column("ai_task_id", sa.String(length=36), nullable=True),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", mysql.LONGTEXT(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("sensitive_redacted", sa.Boolean(), nullable=False),
        sa.Column("retrieval_source", sa.String(length=50), nullable=True),
        sa.Column("retrieval_error", sa.String(length=500), nullable=True),
        sa.Column("retrieved_chunk_ids", sa.JSON(), nullable=True),
        sa.Column("knowledge_base_version", sa.String(length=100), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("prompt_version", sa.String(length=50), nullable=True),
        sa.Column("answered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ai_task_id"], ["ai_tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["execution_task_id"], ["career_plan_execution_tasks.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ai_task_id"),
        sa.UniqueConstraint(
            "user_id", "execution_task_id", "input_hash", name="uq_career_question_input"
        ),
    )
    op.create_index(
        "ix_career_plan_questions_execution_task_id",
        "career_plan_questions",
        ["execution_task_id"],
    )
    op.create_index("ix_career_plan_questions_status", "career_plan_questions", ["status"])
    op.create_index("ix_career_plan_questions_user_id", "career_plan_questions", ["user_id"])
    op.create_index(
        "ix_career_questions_user_created", "career_plan_questions", ["user_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_table("career_plan_questions")
