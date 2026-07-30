"""create activities table

Revision ID: 0001_create_activities
Revises:
Create Date: 2026-07-30 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_create_activities"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "activities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("aggregate_id", sa.String(length=100), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index("ix_activities_event_id", "activities", ["event_id"])
    op.create_index("ix_activities_event_type", "activities", ["event_type"])
    op.create_index("ix_activities_aggregate_id", "activities", ["aggregate_id"])


def downgrade() -> None:
    op.drop_index("ix_activities_aggregate_id", table_name="activities")
    op.drop_index("ix_activities_event_type", table_name="activities")
    op.drop_index("ix_activities_event_id", table_name="activities")
    op.drop_table("activities")
