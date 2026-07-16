"""add career planning tables and generation audit

Revision ID: d7e9f1a2b3c4
Revises: c3b6e8d1a4f2
Create Date: 2026-07-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "d7e9f1a2b3c4"
down_revision: Union[str, Sequence[str], None] = "c3b6e8d1a4f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    existing_tables = set(sa.inspect(connection).get_table_names())

    if "career_project_attachments" not in existing_tables:
        op.create_table(
            "career_project_attachments",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("original_filename", sa.String(length=255), nullable=False),
            sa.Column("stored_filename", sa.String(length=255), nullable=False),
            sa.Column("file_path", sa.String(length=500), nullable=False),
            sa.Column("file_type", sa.String(length=20), nullable=False),
            sa.Column("file_size", sa.BigInteger(), nullable=False),
            sa.Column("extracted_text", mysql.LONGTEXT(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("error_message", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_career_project_attachments_user_id"),
            "career_project_attachments",
            ["user_id"],
        )

    if "career_planning_profiles" not in existing_tables:
        op.create_table(
            "career_planning_profiles",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("education", sa.String(length=50), nullable=False),
            sa.Column("experience", sa.String(length=50), nullable=False),
            sa.Column("skills", sa.JSON(), nullable=False),
            sa.Column("work_description", mysql.LONGTEXT(), nullable=False),
            sa.Column("weekly_learning_hours", sa.Integer(), nullable=False),
            sa.Column("preferred_target_role", sa.String(length=100), nullable=True),
            sa.Column("projects", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_career_planning_profiles_user_id"),
            "career_planning_profiles",
            ["user_id"],
        )

    if "career_plans" not in existing_tables:
        op.create_table(
            "career_plans",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("profile_id", sa.BigInteger(), nullable=False),
            sa.Column("task_id", sa.String(length=36), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("career_profile_summary", sa.JSON(), nullable=False),
            sa.Column("recommended_roles", sa.JSON(), nullable=False),
            sa.Column("career_goals", sa.JSON(), nullable=False),
            sa.Column("skill_gap_analysis", sa.JSON(), nullable=False),
            sa.Column("learning_path", sa.JSON(), nullable=False),
            sa.Column("action_plan", sa.JSON(), nullable=False),
            sa.Column("risks_and_alternatives", sa.JSON(), nullable=False),
            sa.Column("error_message", sa.String(length=500), nullable=True),
            sa.Column("model_name", sa.String(length=100), nullable=True),
            sa.Column("prompt_version", sa.String(length=50), nullable=True),
            sa.Column("retrieval_source", sa.String(length=50), nullable=True),
            sa.Column("retrieval_error", sa.String(length=500), nullable=True),
            sa.Column("retrieved_chunk_ids", sa.JSON(), nullable=True),
            sa.Column("knowledge_base_version", sa.String(length=100), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["profile_id"], ["career_planning_profiles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["task_id"], ["ai_tasks.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("task_id"),
        )
        op.create_index(op.f("ix_career_plans_profile_id"), "career_plans", ["profile_id"])
        op.create_index(op.f("ix_career_plans_user_id"), "career_plans", ["user_id"])
    else:
        existing_columns = {
            column["name"] for column in sa.inspect(connection).get_columns("career_plans")
        }
        audit_columns = (
            sa.Column("retrieval_source", sa.String(length=50), nullable=True),
            sa.Column("retrieval_error", sa.String(length=500), nullable=True),
            sa.Column("retrieved_chunk_ids", sa.JSON(), nullable=True),
            sa.Column("knowledge_base_version", sa.String(length=100), nullable=True),
        )
        for column in audit_columns:
            if column.name not in existing_columns:
                op.add_column("career_plans", column)

    if "ai_tasks" in existing_tables:
        op.execute(
            "UPDATE ai_tasks SET token_usage = JSON_OBJECT("
            "'prompt_tokens', 0, 'completion_tokens', 0, 'total_tokens', 0, "
            "'usage_reported', false, 'audit_note', 'legacy_usage_unavailable') "
            "WHERE task_type = 'career_plan' AND status = 'success' AND token_usage IS NULL"
        )


def downgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "career_plans" in existing_tables:
        op.drop_table("career_plans")
    if "career_planning_profiles" in existing_tables:
        op.drop_table("career_planning_profiles")
    if "career_project_attachments" in existing_tables:
        op.drop_table("career_project_attachments")
