"""add career plan acceptance, execution and check-ins

Revision ID: e8a2c4d6f901
Revises: d7e9f1a2b3c4
Create Date: 2026-07-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "e8a2c4d6f901"
down_revision: Union[str, Sequence[str], None] = "d7e9f1a2b3c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = set(inspector.get_table_names())
    plan_columns = {column["name"] for column in inspector.get_columns("career_plans")}

    additions = (
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("previous_plan_id", sa.BigInteger(), nullable=True),
        sa.Column("regeneration_feedback", mysql.LONGTEXT(), nullable=True),
        sa.Column("regeneration_focus_areas", sa.JSON(), nullable=True),
    )
    for column in additions:
        if column.name not in plan_columns:
            op.add_column("career_plans", column)

    inspector = sa.inspect(connection)
    foreign_keys = inspector.get_foreign_keys("career_plans")
    has_previous_plan_fk = any(
        fk.get("constrained_columns") == ["previous_plan_id"] for fk in foreign_keys
    )
    if not has_previous_plan_fk:
        op.create_foreign_key(
            "fk_career_plans_previous_plan_id",
            "career_plans",
            "career_plans",
            ["previous_plan_id"],
            ["id"],
            ondelete="SET NULL",
        )
    indexes = {index["name"] for index in inspector.get_indexes("career_plans")}
    if "ix_career_plans_previous_plan_id" not in indexes:
        op.create_index("ix_career_plans_previous_plan_id", "career_plans", ["previous_plan_id"])

    if "career_plan_executions" not in existing_tables:
        op.create_table(
            "career_plan_executions",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("career_plan_id", sa.BigInteger(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["career_plan_id"], ["career_plans.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("career_plan_id"),
        )
        op.create_index("ix_career_plan_executions_status", "career_plan_executions", ["status"])
        op.create_index("ix_career_plan_executions_user_id", "career_plan_executions", ["user_id"])
        op.create_index(
            "ix_career_plan_executions_user_status",
            "career_plan_executions",
            ["user_id", "status"],
        )

    if "career_plan_execution_tasks" not in existing_tables:
        op.create_table(
            "career_plan_execution_tasks",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("execution_plan_id", sa.BigInteger(), nullable=False),
            sa.Column("task_key", sa.String(length=64), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("task_type", sa.String(length=20), nullable=False),
            sa.Column("stage", sa.String(length=200), nullable=False),
            sa.Column("week_no", sa.Integer(), nullable=False),
            sa.Column("planned_date", sa.Date(), nullable=True),
            sa.Column("is_required", sa.Boolean(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("checkin_note", sa.String(length=300), nullable=True),
            sa.Column("checked_in_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["execution_plan_id"], ["career_plan_executions.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "execution_plan_id", "task_key", name="uq_career_execution_task_key"
            ),
        )
        op.create_index(
            "ix_career_execution_tasks_execution_plan_id",
            "career_plan_execution_tasks",
            ["execution_plan_id"],
        )
        op.create_index(
            "ix_career_execution_tasks_planned_date",
            "career_plan_execution_tasks",
            ["planned_date"],
        )
        op.create_index(
            "ix_career_execution_tasks_status", "career_plan_execution_tasks", ["status"]
        )
        op.create_index(
            "ix_career_execution_tasks_user_id", "career_plan_execution_tasks", ["user_id"]
        )
        op.create_index(
            "ix_career_execution_tasks_week",
            "career_plan_execution_tasks",
            ["execution_plan_id", "week_no"],
        )

    if "career_plan_checkins" not in existing_tables:
        op.create_table(
            "career_plan_checkins",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("task_id", sa.BigInteger(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("note", sa.String(length=300), nullable=True),
            sa.Column("checked_in_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["task_id"], ["career_plan_execution_tasks.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_career_plan_checkins_task_id", "career_plan_checkins", ["task_id"])
        op.create_index("ix_career_plan_checkins_user_id", "career_plan_checkins", ["user_id"])


def downgrade() -> None:
    op.drop_table("career_plan_checkins")
    op.drop_table("career_plan_execution_tasks")
    op.drop_table("career_plan_executions")
    op.drop_index("ix_career_plans_previous_plan_id", table_name="career_plans")
    op.drop_constraint("fk_career_plans_previous_plan_id", "career_plans", type_="foreignkey")
    op.drop_column("career_plans", "regeneration_focus_areas")
    op.drop_column("career_plans", "regeneration_feedback")
    op.drop_column("career_plans", "previous_plan_id")
    op.drop_column("career_plans", "accepted_at")
