"""add career plan advance and stage assessments

Revision ID: a0c4e6f8b123
Revises: f9b3d5e7a012
Create Date: 2026-07-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = "a0c4e6f8b123"
down_revision: Union[str, Sequence[str], None] = "f9b3d5e7a012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {item["name"] for item in inspector.get_columns("career_plan_execution_tasks")}
    additions = (
        ("stage_order", sa.Integer(), False, "1"),
        ("task_order", sa.Integer(), False, "0"),
        ("is_active", sa.Boolean(), False, "1"),
        ("is_advanced", sa.Boolean(), False, "0"),
        ("original_planned_date", sa.Date(), True, None),
        ("advanced_at", sa.DateTime(), True, None),
        ("is_remediation", sa.Boolean(), False, "0"),
        ("remediation_assessment_id", sa.BigInteger(), True, None),
    )
    for name, type_, nullable, default in additions:
        if name not in columns:
            op.add_column("career_plan_execution_tasks", sa.Column(name, type_, nullable=nullable, server_default=default))

    tables = set(inspector.get_table_names())
    if "career_stage_progress" not in tables:
        op.create_table(
            "career_stage_progress",
            sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
            sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("execution_plan_id", sa.BigInteger(), sa.ForeignKey("career_plan_executions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("stage", sa.String(200), nullable=False),
            sa.Column("stage_order", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(30), nullable=False),
            sa.Column("passed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("execution_plan_id", "stage_order", name="uq_career_stage_order"),
        )
        op.create_index("ix_career_stage_progress_user_id", "career_stage_progress", ["user_id"])
        op.create_index("ix_career_stage_progress_execution_plan_id", "career_stage_progress", ["execution_plan_id"])
        op.create_index("ix_career_stage_progress_status", "career_stage_progress", ["status"])
    if "career_stage_assessments" not in tables:
        op.create_table(
            "career_stage_assessments",
            sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
            sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("execution_plan_id", sa.BigInteger(), sa.ForeignKey("career_plan_executions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("stage_progress_id", sa.BigInteger(), sa.ForeignKey("career_stage_progress.id", ondelete="CASCADE"), nullable=False),
            sa.Column("generation_task_id", sa.String(36), sa.ForeignKey("ai_tasks.id", ondelete="SET NULL"), unique=True),
            sa.Column("evaluation_task_id", sa.String(36), sa.ForeignKey("ai_tasks.id", ondelete="SET NULL"), unique=True),
            sa.Column("stage", sa.String(200), nullable=False), sa.Column("stage_order", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(30), nullable=False), sa.Column("passing_score", sa.Integer(), nullable=False),
            sa.Column("time_limit_minutes", sa.Integer()), sa.Column("score", sa.Integer()),
            sa.Column("summary", mysql.LONGTEXT()), sa.Column("strengths", sa.JSON()), sa.Column("weaknesses", sa.JSON()),
            sa.Column("improvement_advice", sa.JSON()), sa.Column("question_results", sa.JSON()),
            sa.Column("submitted_at", sa.DateTime()), sa.Column("evaluated_at", sa.DateTime()), sa.Column("error_message", sa.String(500)),
            sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        for col in ("user_id", "execution_plan_id", "stage_progress_id", "status"):
            op.create_index(f"ix_career_stage_assessments_{col}", "career_stage_assessments", [col])
    if "career_stage_assessment_questions" not in tables:
        op.create_table(
            "career_stage_assessment_questions",
            sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
            sa.Column("assessment_id", sa.BigInteger(), sa.ForeignKey("career_stage_assessments.id", ondelete="CASCADE"), nullable=False),
            sa.Column("question_order", sa.Integer(), nullable=False), sa.Column("question_type", sa.String(20), nullable=False),
            sa.Column("title", sa.Text(), nullable=False), sa.Column("options", sa.JSON()), sa.Column("correct_answer", sa.JSON()),
            sa.Column("reference_answer", mysql.LONGTEXT()), sa.Column("rubric", mysql.LONGTEXT()), sa.Column("points", sa.Integer(), nullable=False),
            sa.Column("code_language", sa.String(30)), sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("assessment_id", "question_order", name="uq_career_assessment_question_order"),
        )
        op.create_index("ix_career_stage_assessment_questions_assessment_id", "career_stage_assessment_questions", ["assessment_id"])
    if "career_stage_assessment_answers" not in tables:
        op.create_table(
            "career_stage_assessment_answers",
            sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
            sa.Column("assessment_id", sa.BigInteger(), sa.ForeignKey("career_stage_assessments.id", ondelete="CASCADE"), nullable=False),
            sa.Column("question_id", sa.BigInteger(), sa.ForeignKey("career_stage_assessment_questions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("answer", sa.JSON(), nullable=False), sa.Column("rule_score", sa.Integer()), sa.Column("ai_score", sa.Integer()),
            sa.Column("final_score", sa.Integer()), sa.Column("scoring_rationale", mysql.LONGTEXT()), sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("assessment_id", "question_id", name="uq_career_assessment_answer"),
        )
        for col in ("assessment_id", "question_id", "user_id"):
            op.create_index(f"ix_career_stage_assessment_answers_{col}", "career_stage_assessment_answers", [col])


def downgrade() -> None:
    for table in ("career_stage_assessment_answers", "career_stage_assessment_questions", "career_stage_assessments", "career_stage_progress"):
        op.drop_table(table)
    for name in ("remediation_assessment_id", "is_remediation", "advanced_at", "original_planned_date", "is_advanced", "is_active", "task_order", "stage_order"):
        op.drop_column("career_plan_execution_tasks", name)
