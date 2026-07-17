"""add profile security and preferences

Revision ID: d5e9f3a7b246
Revises: c4d8e2f6a135
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d5e9f3a7b246"
down_revision: Union[str, None] = "c4d8e2f6a135"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("users")}
    additions = [
        ("email_verified", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false())),
        ("phone_verified", sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default=sa.false())),
        ("two_factor_enabled", sa.Column("two_factor_enabled", sa.Boolean(), nullable=False, server_default=sa.false())),
        ("two_factor_secret_encrypted", sa.Column("two_factor_secret_encrypted", sa.Text(), nullable=True)),
        ("two_factor_pending_secret_encrypted", sa.Column("two_factor_pending_secret_encrypted", sa.Text(), nullable=True)),
        ("auth_version", sa.Column("auth_version", sa.Integer(), nullable=False, server_default="0")),
        ("last_login_at", sa.Column("last_login_at", sa.DateTime(), nullable=True)),
    ]
    for name, column in additions:
        if name not in columns:
            op.add_column("users", column)
    tables = set(inspector.get_table_names())
    if "user_preferences" not in tables:
        op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("email_notifications", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("push_notifications", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("ai_report_notifications", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
        )
    if "two_factor_recovery_codes" not in tables:
        op.create_table(
        "two_factor_recovery_codes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("code_hash", sa.String(255), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        )
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("two_factor_recovery_codes")}
    if "ix_two_factor_recovery_codes_user_id" not in indexes:
        op.create_index("ix_two_factor_recovery_codes_user_id", "two_factor_recovery_codes", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_two_factor_recovery_codes_user_id", table_name="two_factor_recovery_codes")
    op.drop_table("two_factor_recovery_codes")
    op.drop_table("user_preferences")
    for name in ["last_login_at", "auth_version", "two_factor_pending_secret_encrypted", "two_factor_secret_encrypted", "two_factor_enabled", "phone_verified", "email_verified"]:
        op.drop_column("users", name)
