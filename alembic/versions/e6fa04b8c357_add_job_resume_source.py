"""add resume source to recommendation and application records

Revision ID: e6fa04b8c357
Revises: d5e9f3a7b246
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e6fa04b8c357"
down_revision: Union[str, None] = "d5e9f3a7b246"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = ("job_applications", "job_platform_login_sessions", "job_recommend_tasks")


def upgrade() -> None:
    for table in TABLES:
        inspector = sa.inspect(op.get_bind())
        columns = {column["name"] for column in inspector.get_columns(table)}
        if "resume_source" not in columns:
            op.add_column(
                table,
                sa.Column("resume_source", sa.String(20), nullable=False, server_default="original"),
            )
        if "resume_optimization_id" not in columns:
            op.add_column(table, sa.Column("resume_optimization_id", sa.BigInteger(), nullable=True))
        inspector = sa.inspect(op.get_bind())
        foreign_columns = {
            tuple(fk.get("constrained_columns") or [])
            for fk in inspector.get_foreign_keys(table)
        }
        if ("resume_optimization_id",) not in foreign_columns:
            op.create_foreign_key(
                f"fk_{table}_resume_optimization_id",
                table,
                "resume_optimization_versions",
                ["resume_optimization_id"],
                ["id"],
                ondelete="SET NULL",
            )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_constraint(f"fk_{table}_resume_optimization_id", table, type_="foreignkey")
        op.drop_column(table, "resume_optimization_id")
        op.drop_column(table, "resume_source")
