from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.gpuaas.app.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from apps.gpuaas.app.models.customer import Customer
    from apps.gpuaas.app.models.job import GPUJob


class GPUAllocation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "gpu_allocations"

    customer_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    gpu_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    gpu_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    region: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        server_default="active",
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="allocations",
    )

    jobs: Mapped[list["GPUJob"]] = relationship(
        back_populates="allocation",
    )
