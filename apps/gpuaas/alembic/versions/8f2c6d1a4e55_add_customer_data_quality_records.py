"""add customer data quality records

Revision ID: 8f2c6d1a4e55
Revises: 7e1c4a9b2d33
Create Date: 2026-08-19 08:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8f2c6d1a4e55"
down_revision: Union[str, Sequence[str], None] = "7e1c4a9b2d33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customer_data_quality_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column(
            "source",
            sa.String(length=50),
            nullable=False,
        ),
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
            "status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "mismatches",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "missing",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "fields",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "checked_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
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
        sa.UniqueConstraint(
            "customer_id",
            "source",
            "entity_type",
            "external_id",
            name="uq_customer_dq_customer_source_identity",
        ),
    )

    op.create_index(
        "ix_customer_data_quality_records_customer_id",
        "customer_data_quality_records",
        ["customer_id"],
        unique=False,
    )

    op.create_index(
        "ix_customer_data_quality_records_source",
        "customer_data_quality_records",
        ["source"],
        unique=False,
    )

    op.create_index(
        "ix_customer_data_quality_records_external_id",
        "customer_data_quality_records",
        ["external_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_customer_data_quality_records_external_id",
        table_name="customer_data_quality_records",
    )

    op.drop_index(
        "ix_customer_data_quality_records_source",
        table_name="customer_data_quality_records",
    )

    op.drop_index(
        "ix_customer_data_quality_records_customer_id",
        table_name="customer_data_quality_records",
    )

    op.drop_table(
        "customer_data_quality_records"
    )
