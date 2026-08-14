import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from apps.integration_hub.app.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class IntegrationEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "integration_events"

    __table_args__ = (
        UniqueConstraint(
            "source",
            "source_event_id",
            name="uq_integration_events_source_event",
        ),
        Index(
            "ix_integration_events_event_type_occurred_at",
            "event_type",
            "occurred_at",
        ),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    source_event_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    correlation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="received",
        server_default="received",
        index=True,
    )

    retry_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default="0",
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
