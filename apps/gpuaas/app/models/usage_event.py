from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.gpuaas.app.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from apps.gpuaas.app.models.allocation import GPUAllocation
    from apps.gpuaas.app.models.customer import Customer


class GPUUsageEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "gpu_usage_events"

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            name="uq_gpu_usage_events_event_id",
        ),
    )

    event_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    allocation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gpu_allocations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    gpu_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    gpu_hours: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    utilization: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    customer: Mapped["Customer"] = relationship()

    allocation: Mapped["GPUAllocation"] = relationship()
