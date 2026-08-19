"""add customer reconciliation runs

Revision ID: a4c8e2f6b711
Revises: 9b3e7f1c5a66
Create Date: 2026-08-19 09:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4c8e2f6b711"
down_revision: Union[str, Sequence[str], None] = "9b3e7f1c5a66"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customer_reconciliation_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "processed",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "succeeded",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "failed",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_customer_reconciliation_runs_status",
        "customer_reconciliation_runs",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_customer_reconciliation_runs_status",
        table_name="customer_reconciliation_runs",
    )

    op.drop_table(
        "customer_reconciliation_runs"
    )
