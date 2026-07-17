"""add HR interview coordination

Revision ID: b9cd20e3f652
Revises: a8bc19d2e541
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b9cd20e3f652"
down_revision: Union[str, None] = "a8bc19d2e541"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if "hr_interviews" in set(sa.inspect(bind).get_table_names()):
        return
    op.create_table(
        "hr_interviews",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("source_message_id", sa.BigInteger(), nullable=True),
        sa.Column("action_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="proposed"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("end_at", sa.DateTime(), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="Asia/Shanghai"),
        sa.Column("interview_type", sa.String(50), nullable=True),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("meeting_url", sa.String(500), nullable=True),
        sa.Column("contact_name", sa.String(100), nullable=True),
        sa.Column("evidence", sa.String(1000), nullable=True),
        sa.Column("missing_fields", sa.JSON(), nullable=True),
        sa.Column("suggested_reply", sa.Text(), nullable=True),
        sa.Column("requires_confirmation", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["hr_workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_message_id"], ["hr_messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["action_id"], ["hr_pending_actions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hr_interviews_workspace_id", "hr_interviews", ["workspace_id"])
    op.create_index("ix_hr_interviews_user_id", "hr_interviews", ["user_id"])
    op.create_index("ix_hr_interviews_status", "hr_interviews", ["status"])
    op.create_index("ix_hr_interviews_scheduled_at", "hr_interviews", ["scheduled_at"])
    op.create_index("ix_hr_interviews_user_schedule", "hr_interviews", ["user_id", "scheduled_at"])


def downgrade() -> None:
    if "hr_interviews" in set(sa.inspect(op.get_bind()).get_table_names()):
        op.drop_table("hr_interviews")
