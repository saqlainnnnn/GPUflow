"""add customer data quality audits

Revision ID: b7d4e9f2c813
Revises: a4c8e2f6b711
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7d4e9f2c813"
down_revision: Union[str, Sequence[str], None] = "a4c8e2f6b711"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customer_data_quality_audits",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column(
            "entity_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "external_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "field",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "decision",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "ownership",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "canonical_value",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "source_value",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "resolved_value",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "resolved_at",
            sa.DateTime(timezone=True),
            nullable=False,
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
        "ix_customer_data_quality_audits_customer_id",
        "customer_data_quality_audits",
        ["customer_id"],
        unique=False,
    )

    op.create_index(
        "ix_customer_data_quality_audits_source",
        "customer_data_quality_audits",
        ["source"],
        unique=False,
    )

    op.create_index(
        "ix_customer_data_quality_audits_external_id",
        "customer_data_quality_audits",
        ["external_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_customer_data_quality_audits_external_id",
        table_name="customer_data_quality_audits",
    )

    op.drop_index(
        "ix_customer_data_quality_audits_source",
        table_name="customer_data_quality_audits",
    )

    op.drop_index(
        "ix_customer_data_quality_audits_customer_id",
        table_name="customer_data_quality_audits",
    )

    op.drop_table(
        "customer_data_quality_audits"
    )
