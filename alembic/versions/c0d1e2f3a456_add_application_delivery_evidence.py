"""add application delivery evidence and user/job uniqueness

Revision ID: c0d1e2f3a456
Revises: b9cd20e3f652
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c0d1e2f3a456"
down_revision: Union[str, None] = "b9cd20e3f652"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("job_applications")}
    if "delivery_evidence" not in columns:
        op.add_column("job_applications", sa.Column("delivery_evidence", sa.JSON(), nullable=True))

    unique_names = {
        constraint.get("name")
        for constraint in inspector.get_unique_constraints("job_applications")
    }
    if "uq_job_applications_user_job" not in unique_names:
        if bind.dialect.name == "mysql":
            op.execute(sa.text(
                "DELETE newer FROM job_applications newer "
                "JOIN job_applications older "
                "ON newer.user_id = older.user_id "
                "AND newer.job_id = older.job_id "
                "AND newer.id > older.id"
            ))
        else:
            op.execute(sa.text(
                "DELETE FROM job_applications WHERE id NOT IN ("
                "SELECT keep_id FROM ("
                "SELECT MIN(id) AS keep_id FROM job_applications GROUP BY user_id, job_id"
                ") AS deduplicated)"
            ))
        op.create_unique_constraint(
            "uq_job_applications_user_job",
            "job_applications",
            ["user_id", "job_id"],
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    unique_names = {
        constraint.get("name")
        for constraint in inspector.get_unique_constraints("job_applications")
    }
    if "uq_job_applications_user_job" in unique_names:
        op.drop_constraint(
            "uq_job_applications_user_job",
            "job_applications",
            type_="unique",
        )
    columns = {column["name"] for column in inspector.get_columns("job_applications")}
    if "delivery_evidence" in columns:
        op.drop_column("job_applications", "delivery_evidence")
