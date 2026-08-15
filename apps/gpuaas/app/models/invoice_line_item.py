from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.gpuaas.app.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from apps.gpuaas.app.models.invoice import Invoice


class InvoiceLineItem(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "invoice_line_items"

    invoice_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    gpu_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    gpu_hours: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
    )

    rate_per_gpu_hour: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    invoice: Mapped["Invoice"] = relationship(
        back_populates="line_items",
    )
