"""add kyb audits

Revision ID: c8e5f1a7d924
Revises: b7d4e9f2c813
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8e5f1a7d924"
down_revision: Union[str, Sequence[str], None] = "b7d4e9f2c813"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kyb_audits",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "customer_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "check_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "input_snapshot",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "decision",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "reason",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "reviewer",
            sa.String(length=255),
            nullable=True,
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
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_kyb_audits_customer_id",
        "kyb_audits",
        ["customer_id"],
        unique=False,
    )

    op.create_index(
        "ix_kyb_audits_check_type",
        "kyb_audits",
        ["check_type"],
        unique=False,
    )

    op.create_index(
        "ix_kyb_audits_decision",
        "kyb_audits",
        ["decision"],
        unique=False,
    )

    op.create_index(
        "ix_kyb_audits_timestamp",
        "kyb_audits",
        ["timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_kyb_audits_timestamp",
        table_name="kyb_audits",
    )

    op.drop_index(
        "ix_kyb_audits_decision",
        table_name="kyb_audits",
    )

    op.drop_index(
        "ix_kyb_audits_check_type",
        table_name="kyb_audits",
    )

    op.drop_index(
        "ix_kyb_audits_customer_id",
        table_name="kyb_audits",
    )

    op.drop_table("kyb_audits")
