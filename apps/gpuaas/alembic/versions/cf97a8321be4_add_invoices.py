"""add invoices

Revision ID: cf97a8321be4
Revises: 63edb6577f88
Create Date: 2026-08-15 20:47:59.561534

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cf97a8321be4"
down_revision: str | Sequence[str] | None = "63edb6577f88"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "invoices",
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column(
            "invoice_number",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "period_start",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "period_end",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            server_default="USD",
            nullable=False,
        ),
        sa.Column(
            "subtotal",
            sa.Numeric(precision=12, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "total",
            sa.Numeric(precision=12, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default="draft",
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "customer_id",
            "period_start",
            "period_end",
            name="uq_invoice_customer_period",
        ),
    )

    op.create_index(
        op.f("ix_invoices_customer_id"),
        "invoices",
        ["customer_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_invoices_invoice_number"),
        "invoices",
        ["invoice_number"],
        unique=True,
    )

    op.create_index(
        op.f("ix_invoices_status"),
        "invoices",
        ["status"],
        unique=False,
    )

    op.create_table(
        "invoice_line_items",
        sa.Column("invoice_id", sa.UUID(), nullable=False),
        sa.Column(
            "description",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "gpu_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "gpu_hours",
            sa.Numeric(precision=12, scale=4),
            nullable=False,
        ),
        sa.Column(
            "rate_per_gpu_hour",
            sa.Numeric(precision=12, scale=4),
            nullable=False,
        ),
        sa.Column(
            "amount",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["invoices.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_invoice_line_items_invoice_id"),
        "invoice_line_items",
        ["invoice_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_invoice_line_items_invoice_id"),
        table_name="invoice_line_items",
    )
    op.drop_table("invoice_line_items")

    op.drop_index(
        op.f("ix_invoices_status"),
        table_name="invoices",
    )
    op.drop_index(
        op.f("ix_invoices_invoice_number"),
        table_name="invoices",
    )
    op.drop_index(
        op.f("ix_invoices_customer_id"),
        table_name="invoices",
    )
    op.drop_table("invoices")
