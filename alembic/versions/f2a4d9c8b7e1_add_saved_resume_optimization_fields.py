'''add saved resume optimization fields

Revision ID: f2a4d9c8b7e1
Revises: c842c7b923f1
Create Date: 2026-07-15
'''
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f2a4d9c8b7e1'
down_revision: Union[str, Sequence[str], None] = 'c842c7b923f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('resume_optimization_versions', sa.Column('title', sa.String(length=200), nullable=True))
    op.add_column('resume_optimization_versions', sa.Column('is_saved', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('resume_optimization_versions', sa.Column('saved_at', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_resume_optimization_versions_is_saved'), 'resume_optimization_versions', ['is_saved'])
    op.alter_column('resume_optimization_versions', 'is_saved', server_default=None)


def downgrade() -> None:
    op.drop_index(op.f('ix_resume_optimization_versions_is_saved'), table_name='resume_optimization_versions')
    op.drop_column('resume_optimization_versions', 'saved_at')
    op.drop_column('resume_optimization_versions', 'is_saved')
    op.drop_column('resume_optimization_versions', 'title')
