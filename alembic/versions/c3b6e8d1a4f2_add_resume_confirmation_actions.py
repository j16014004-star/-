"""add resume confirmation actions

Revision ID: c3b6e8d1a4f2
Revises: f2a4d9c8b7e1
Create Date: 2026-07-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3b6e8d1a4f2'
down_revision: Union[str, Sequence[str], None] = 'f2a4d9c8b7e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'resume_optimization_versions',
        sa.Column('confirmation_actions', sa.JSON(), nullable=True),
    )
    op.execute(
        "UPDATE resume_optimization_versions "
        "SET confirmation_actions = JSON_ARRAY() "
        "WHERE confirmation_actions IS NULL"
    )
    op.alter_column(
        'resume_optimization_versions',
        'confirmation_actions',
        existing_type=sa.JSON(),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column('resume_optimization_versions', 'confirmation_actions')
