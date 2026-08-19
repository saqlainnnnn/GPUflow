"""add customer data quality issues

Revision ID: 9b3e7f1c5a66
Revises: 8f2c6d1a4e55
Create Date: 2026-08-19 08:45:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b3e7f1c5a66"
down_revision: Union[str, Sequence[str], None] = "8f2c6d1a4e55"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customer_data_quality_issues",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "customer_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "issue_type",
            sa.String(length=50),
            nullable=False,
        ),
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
            server_default=sa.text("'open'"),
        ),
        sa.Column(
            "details",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "resolved_at",
            sa.DateTime(timezone=True),
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
        sa.UniqueConstraint(
            "issue_type",
            "source",
            "entity_type",
            "external_id",
            name="uq_customer_dq_issue_identity",
        ),
    )

    op.create_index(
        "ix_customer_data_quality_issues_customer_id",
        "customer_data_quality_issues",
        ["customer_id"],
        unique=False,
    )

    op.create_index(
        "ix_customer_data_quality_issues_issue_type",
        "customer_data_quality_issues",
        ["issue_type"],
        unique=False,
    )

    op.create_index(
        "ix_customer_data_quality_issues_source",
        "customer_data_quality_issues",
        ["source"],
        unique=False,
    )

    op.create_index(
        "ix_customer_data_quality_issues_external_id",
        "customer_data_quality_issues",
        ["external_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_customer_data_quality_issues_external_id",
        table_name="customer_data_quality_issues",
    )

    op.drop_index(
        "ix_customer_data_quality_issues_source",
        table_name="customer_data_quality_issues",
    )

    op.drop_index(
        "ix_customer_data_quality_issues_issue_type",
        table_name="customer_data_quality_issues",
    )

    op.drop_index(
        "ix_customer_data_quality_issues_customer_id",
        table_name="customer_data_quality_issues",
    )

    op.drop_table(
        "customer_data_quality_issues"
    )
