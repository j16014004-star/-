'''add resume optimization tables

Revision ID: c842c7b923f1
Revises: bcb099662339
Create Date: 2026-07-15
'''
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = 'c842c7b923f1'
down_revision: Union[str, Sequence[str], None] = 'bcb099662339'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_tasks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=30), nullable=False),
        sa.Column('resource_id', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False),
        sa.Column('result_id', sa.BigInteger(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('prompt_version', sa.String(length=50), nullable=False),
        sa.Column('input_hash', sa.String(length=64), nullable=False),
        sa.Column('request_payload', sa.JSON(), nullable=True),
        sa.Column('token_usage', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('provider_call_started_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ai_tasks_idempotency', 'ai_tasks', ['user_id', 'task_type', 'resource_id', 'input_hash'])
    op.create_index(op.f('ix_ai_tasks_input_hash'), 'ai_tasks', ['input_hash'])
    op.create_index(op.f('ix_ai_tasks_resource_id'), 'ai_tasks', ['resource_id'])
    op.create_index(op.f('ix_ai_tasks_status'), 'ai_tasks', ['status'])
    op.create_index(op.f('ix_ai_tasks_task_type'), 'ai_tasks', ['task_type'])
    op.create_index(op.f('ix_ai_tasks_user_id'), 'ai_tasks', ['user_id'])

    op.create_table(
        'resume_optimization_versions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('resume_id', sa.BigInteger(), nullable=False),
        sa.Column('task_id', sa.String(length=36), nullable=False),
        sa.Column('analysis_id', sa.BigInteger(), nullable=True),
        sa.Column('optimization_type', sa.String(length=30), nullable=False),
        sa.Column('target_role', sa.String(length=100), nullable=True),
        sa.Column('optimization_focus', sa.JSON(), nullable=False),
        sa.Column('style', sa.String(length=30), nullable=False),
        sa.Column('preserve_structure', sa.Boolean(), nullable=False),
        sa.Column('optimization_summary', sa.Text(), nullable=False),
        sa.Column('original_content', mysql.LONGTEXT(), nullable=False),
        sa.Column('optimized_content', mysql.LONGTEXT(), nullable=False),
        sa.Column('change_items', sa.JSON(), nullable=False),
        sa.Column('confirmation_questions', sa.JSON(), nullable=False),
        sa.Column('score_improvement', sa.Integer(), nullable=True),
        sa.Column('knowledge_base_version', sa.String(length=100), nullable=True),
        sa.Column('retrieved_chunk_ids', sa.JSON(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('embedding_model', sa.String(length=100), nullable=True),
        sa.Column('prompt_version', sa.String(length=50), nullable=False),
        sa.Column('resume_content_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['ai_tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_id'),
    )
    op.create_index(op.f('ix_resume_optimization_versions_resume_id'), 'resume_optimization_versions', ['resume_id'])
    op.create_index(op.f('ix_resume_optimization_versions_user_id'), 'resume_optimization_versions', ['user_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_resume_optimization_versions_user_id'), table_name='resume_optimization_versions')
    op.drop_index(op.f('ix_resume_optimization_versions_resume_id'), table_name='resume_optimization_versions')
    op.drop_table('resume_optimization_versions')
    op.drop_index(op.f('ix_ai_tasks_user_id'), table_name='ai_tasks')
    op.drop_index(op.f('ix_ai_tasks_task_type'), table_name='ai_tasks')
    op.drop_index(op.f('ix_ai_tasks_status'), table_name='ai_tasks')
    op.drop_index(op.f('ix_ai_tasks_resource_id'), table_name='ai_tasks')
    op.drop_index(op.f('ix_ai_tasks_input_hash'), table_name='ai_tasks')
    op.drop_index('ix_ai_tasks_idempotency', table_name='ai_tasks')
    op.drop_table('ai_tasks')
