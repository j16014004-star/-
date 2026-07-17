"""add durable HR platform synchronization state

Revision ID: d2f4a6b8c013
Revises: c0d1e2f3a456
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2f4a6b8c013"
down_revision: Union[str, None] = "c0d1e2f3a456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("hr_workspaces")}
    additions = (
        ("platform_conversation_id", sa.Column("platform_conversation_id", sa.String(200))),
        ("platform_snapshot", sa.Column("platform_snapshot", sa.JSON())),
        (
            "sync_status",
            sa.Column("sync_status", sa.String(30), nullable=False, server_default="never"),
        ),
        ("sync_error", sa.Column("sync_error", sa.String(500))),
        ("last_synced_at", sa.Column("last_synced_at", sa.DateTime())),
    )
    for name, column in additions:
        if name not in columns:
            op.add_column("hr_workspaces", column)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("hr_workspaces")}
    for name in (
        "last_synced_at",
        "sync_error",
        "sync_status",
        "platform_snapshot",
        "platform_conversation_id",
    ):
        if name in columns:
            op.drop_column("hr_workspaces", name)
