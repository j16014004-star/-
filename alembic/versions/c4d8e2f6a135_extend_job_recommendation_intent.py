"""extend job recommendation intent and diagnostics

Revision ID: c4d8e2f6a135
Revises: b1d5f7a9c234
Create Date: 2026-07-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4d8e2f6a135"
down_revision: Union[str, Sequence[str], None] = "b1d5f7a9c234"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_recommend_tasks", sa.Column("target_role", sa.String(100), nullable=True))
    op.add_column("job_recommend_tasks", sa.Column("target_city", sa.String(50), nullable=True))
    op.add_column("job_recommend_tasks", sa.Column("failure_code", sa.String(50), nullable=True))
    op.add_column("job_recommend_tasks", sa.Column("crawl_diagnostics", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("job_recommend_tasks", "crawl_diagnostics")
    op.drop_column("job_recommend_tasks", "failure_code")
    op.drop_column("job_recommend_tasks", "target_city")
    op.drop_column("job_recommend_tasks", "target_role")
