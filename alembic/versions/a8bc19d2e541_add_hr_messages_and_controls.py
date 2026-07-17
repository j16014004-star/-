"""add HR messages and conversation controls

Revision ID: a8bc19d2e541
Revises: f7ab08c9d410
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a8bc19d2e541"
down_revision: Union[str, None] = "f7ab08c9d410"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("hr_workspaces")}
    if "platform_thread_url" not in columns:
        op.add_column("hr_workspaces", sa.Column("platform_thread_url", sa.String(500), nullable=True))
    if "hr_messages" not in set(sa.inspect(bind).get_table_names()):
        op.create_table(
            "hr_messages",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("workspace_id", sa.BigInteger(), nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("action_id", sa.BigInteger(), nullable=True),
            sa.Column("sender_type", sa.String(20), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="pending_confirmation"),
            sa.Column("is_ai_generated", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("requires_confirmation", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("platform_message_ref", sa.String(200), nullable=True),
            sa.Column("sent_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["workspace_id"], ["hr_workspaces.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["action_id"], ["hr_pending_actions.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_hr_messages_workspace_id", "hr_messages", ["workspace_id"])
        op.create_index("ix_hr_messages_user_id", "hr_messages", ["user_id"])
        op.create_index("ix_hr_messages_workspace_created", "hr_messages", ["workspace_id", "created_at"])


def downgrade() -> None:
    bind = op.get_bind()
    if "hr_messages" in set(sa.inspect(bind).get_table_names()):
        op.drop_table("hr_messages")
    columns = {c["name"] for c in sa.inspect(bind).get_columns("hr_workspaces")}
    if "platform_thread_url" in columns:
        op.drop_column("hr_workspaces", "platform_thread_url")
