"""Create review table.

Revision ID: e7c4a8f0b1a2
Revises:
Create Date: 2026-04-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "e7c4a8f0b1a2"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "review",
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("review_date", sa.DateTime(), nullable=False),
        sa.Column("review_text", sa.String(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("classification", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_review_date", "review", ["review_date"], unique=False)
    op.create_index(
        "ix_review_classification", "review", ["classification"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_review_classification", table_name="review")
    op.drop_index("ix_review_review_date", table_name="review")
    op.drop_table("review")
