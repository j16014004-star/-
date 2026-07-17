"""add HR assistant phase one workspaces and confirmation actions

Revision ID: f7ab08c9d410
Revises: e6fa04b8c357
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f7ab08c9d410"
down_revision: Union[str, None] = "e6fa04b8c357"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    login_columns = {
        column["name"] for column in inspector.get_columns("job_platform_login_sessions")
    }
    if "manual_login_verified" not in login_columns:
        op.add_column(
            "job_platform_login_sessions",
            sa.Column(
                "manual_login_verified",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )
    if "manual_login_verified_at" not in login_columns:
        op.add_column(
            "job_platform_login_sessions",
            sa.Column("manual_login_verified_at", sa.DateTime(), nullable=True),
        )
    op.execute(
        sa.text(
            "UPDATE job_platform_login_sessions "
            "SET manual_login_verified = 1, "
            "manual_login_verified_at = COALESCE(manual_login_verified_at, updated_at) "
            "WHERE status = 'logged_in' AND storage_state_ref IS NOT NULL"
        )
    )

    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "hr_workspaces" not in tables:
        op.create_table(
            "hr_workspaces",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("job_id", sa.BigInteger(), nullable=False),
            sa.Column("source", sa.String(20), nullable=False, server_default="58"),
            sa.Column("resume_id", sa.BigInteger(), nullable=False),
            sa.Column("resume_source", sa.String(20), nullable=False, server_default="original"),
            sa.Column("resume_optimization_id", sa.BigInteger(), nullable=True),
            sa.Column("login_session_id", sa.String(36), nullable=True),
            sa.Column("ai_task_id", sa.String(36), nullable=True),
            sa.Column("automation_mode", sa.String(20), nullable=False, server_default="assisted"),
            sa.Column("permissions", sa.JSON(), nullable=False),
            sa.Column("manual_login_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
            sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("current_step", sa.String(200), nullable=True),
            sa.Column("hr_name", sa.String(100), nullable=True),
            sa.Column("unread_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("pending_confirmation_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_message", sa.String(500), nullable=True),
            sa.Column("last_message_at", sa.DateTime(), nullable=True),
            sa.Column("error_message", sa.String(500), nullable=True),
            sa.Column("applied_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["resume_optimization_id"], ["resume_optimization_versions.id"], ondelete="SET NULL"
            ),
            sa.ForeignKeyConstraint(
                ["login_session_id"], ["job_platform_login_sessions.id"], ondelete="SET NULL"
            ),
            sa.ForeignKeyConstraint(["ai_task_id"], ["ai_tasks.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_hr_workspaces_user_id", "hr_workspaces", ["user_id"])
        op.create_index("ix_hr_workspaces_job_id", "hr_workspaces", ["job_id"])
        op.create_index("ix_hr_workspaces_resume_id", "hr_workspaces", ["resume_id"])
        op.create_index("ix_hr_workspaces_status", "hr_workspaces", ["status"])
        op.create_index("ix_hr_workspaces_user_status", "hr_workspaces", ["user_id", "status"])
        op.create_index(
            "ix_hr_workspaces_selection", "hr_workspaces", ["user_id", "job_id", "resume_id"]
        )

    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "hr_pending_actions" not in tables:
        op.create_table(
            "hr_pending_actions",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("workspace_id", sa.BigInteger(), nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("action_type", sa.String(50), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="waiting_confirmation"),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("reason", sa.String(500), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("requires_confirmation", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("idempotency_key", sa.String(64), nullable=False),
            sa.Column("confirmation_note", sa.String(500), nullable=True),
            sa.Column("approved_at", sa.DateTime(), nullable=True),
            sa.Column("executed_at", sa.DateTime(), nullable=True),
            sa.Column("error_message", sa.String(500), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["workspace_id"], ["hr_workspaces.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("idempotency_key", name="uq_hr_pending_actions_idempotency_key"),
        )
        op.create_index("ix_hr_pending_actions_workspace_id", "hr_pending_actions", ["workspace_id"])
        op.create_index("ix_hr_pending_actions_user_id", "hr_pending_actions", ["user_id"])
        op.create_index("ix_hr_pending_actions_status", "hr_pending_actions", ["status"])

    inspector = sa.inspect(bind)
    if "hr_action_logs" not in set(inspector.get_table_names()):
        op.create_table(
            "hr_action_logs",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("workspace_id", sa.BigInteger(), nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("action", sa.String(100), nullable=False),
            sa.Column("description", sa.String(1000), nullable=False),
            sa.Column("status", sa.String(30), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["workspace_id"], ["hr_workspaces.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_hr_action_logs_workspace_id", "hr_action_logs", ["workspace_id"])
        op.create_index("ix_hr_action_logs_user_id", "hr_action_logs", ["user_id"])
        op.create_index("ix_hr_action_logs_status", "hr_action_logs", ["status"])


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    for table in ("hr_action_logs", "hr_pending_actions", "hr_workspaces"):
        if table in tables:
            op.drop_table(table)
    inspector = sa.inspect(bind)
    columns = {
        column["name"] for column in inspector.get_columns("job_platform_login_sessions")
    }
    if "manual_login_verified_at" in columns:
        op.drop_column("job_platform_login_sessions", "manual_login_verified_at")
    if "manual_login_verified" in columns:
        op.drop_column("job_platform_login_sessions", "manual_login_verified")
