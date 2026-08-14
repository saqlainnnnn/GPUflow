from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from apps.gpuaas.app.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class GPUCapacity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "gpu_capacity"

    __table_args__ = (
        UniqueConstraint(
            "region",
            "gpu_type",
            name="uq_gpu_capacity_region_gpu_type",
        ),
    )

    region: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    gpu_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    total_gpus: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    allocated_gpus: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        server_default="active",
    )

    @property
    def available_gpus(self) -> int:
        return self.total_gpus - self.allocated_gpus
