"""add detailed RAG retrieval audit fields

Revision ID: b1d5f7a9c234
Revises: a0c4e6f8b123
Create Date: 2026-07-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b1d5f7a9c234"
down_revision: Union[str, Sequence[str], None] = "a0c4e6f8b123"
branch_labels = None
depends_on = None


def _add_if_missing(table: str, column: sa.Column) -> None:
    names = {item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}
    if column.name not in names:
        op.add_column(table, column)


def upgrade() -> None:
    _add_if_missing("career_plans", sa.Column("retrieval_audit", sa.JSON(), nullable=True))
    _add_if_missing("career_plan_questions", sa.Column("retrieval_audit", sa.JSON(), nullable=True))
    _add_if_missing("career_stage_assessments", sa.Column("retrieval_audit", sa.JSON(), nullable=True))
    _add_if_missing("resume_optimization_versions", sa.Column("retrieval_source", sa.String(50), nullable=True))
    _add_if_missing("resume_optimization_versions", sa.Column("retrieval_error", sa.String(500), nullable=True))
    _add_if_missing("resume_optimization_versions", sa.Column("retrieval_audit", sa.JSON(), nullable=True))


def downgrade() -> None:
    for table, column in (
        ("resume_optimization_versions", "retrieval_audit"),
        ("resume_optimization_versions", "retrieval_error"),
        ("resume_optimization_versions", "retrieval_source"),
        ("career_stage_assessments", "retrieval_audit"),
        ("career_plan_questions", "retrieval_audit"),
        ("career_plans", "retrieval_audit"),
    ):
        op.drop_column(table, column)
