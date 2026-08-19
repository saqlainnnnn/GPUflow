"""add customer identities

Revision ID: 5d7a9e4c2b11
Revises: 184e24945722
Create Date: 2026-08-19 07:55:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5d7a9e4c2b11"
down_revision: Union[str, Sequence[str], None] = "184e24945722"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customer_identities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source",
            "entity_type",
            "external_id",
            name="uq_customer_identity_source_entity_external",
        ),
        sa.UniqueConstraint(
            "customer_id",
            "source",
            "entity_type",
            name="uq_customer_identity_customer_source_entity",
        ),
    )

    op.create_index(
        "ix_customer_identities_customer_id",
        "customer_identities",
        ["customer_id"],
        unique=False,
    )

    op.create_index(
        "ix_customer_identities_source",
        "customer_identities",
        ["source"],
        unique=False,
    )

    op.create_index(
        "ix_customer_identities_external_id",
        "customer_identities",
        ["external_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_customer_identities_external_id",
        table_name="customer_identities",
    )

    op.drop_index(
        "ix_customer_identities_source",
        table_name="customer_identities",
    )

    op.drop_index(
        "ix_customer_identities_customer_id",
        table_name="customer_identities",
    )

    op.drop_table("customer_identities")
