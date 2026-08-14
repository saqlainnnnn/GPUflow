from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String
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


class GPUJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "gpu_jobs"

    external_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
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

    gpu_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    failure_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="jobs",
    )

    allocation: Mapped["GPUAllocation"] = relationship(
        back_populates="jobs",
    )
