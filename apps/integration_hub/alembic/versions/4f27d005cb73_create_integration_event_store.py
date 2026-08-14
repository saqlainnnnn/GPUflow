"""create integration event store

Revision ID: initial_integration_events
Revises:
Create Date: 2026-08-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "4f27d005cb73"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "integration_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "event_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "source_event_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "correlation_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default="received",
            nullable=False,
        ),
        sa.Column(
            "retry_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "last_error",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "payload",
            postgresql.JSONB(),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
        sa.UniqueConstraint(
            "source",
            "source_event_id",
            name="uq_integration_events_source_event",
        ),
    )

    op.create_index(
        "ix_integration_events_event_id",
        "integration_events",
        ["event_id"],
        unique=False,
    )
    op.create_index(
        "ix_integration_events_event_type",
        "integration_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_integration_events_source",
        "integration_events",
        ["source"],
        unique=False,
    )
    op.create_index(
        "ix_integration_events_occurred_at",
        "integration_events",
        ["occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_integration_events_correlation_id",
        "integration_events",
        ["correlation_id"],
        unique=False,
    )
    op.create_index(
        "ix_integration_events_status",
        "integration_events",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_integration_events_event_type_occurred_at",
        "integration_events",
        ["event_type", "occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_integration_events_event_type_occurred_at",
        table_name="integration_events",
    )
    op.drop_index(
        "ix_integration_events_status",
        table_name="integration_events",
    )
    op.drop_index(
        "ix_integration_events_correlation_id",
        table_name="integration_events",
    )
    op.drop_index(
        "ix_integration_events_occurred_at",
        table_name="integration_events",
    )
    op.drop_index(
        "ix_integration_events_source",
        table_name="integration_events",
    )
    op.drop_index(
        "ix_integration_events_event_type",
        table_name="integration_events",
    )
    op.drop_index(
        "ix_integration_events_event_id",
        table_name="integration_events",
    )
    op.drop_table("integration_events")
