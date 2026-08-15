from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.gpuaas.app.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from apps.gpuaas.app.models.customer import Customer
    from apps.gpuaas.app.models.invoice_line_item import InvoiceLineItem


class Invoice(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "invoices"

    __table_args__ = (
        UniqueConstraint(
            "customer_id",
            "period_start",
            "period_end",
            name="uq_invoice_customer_period",
        ),
    )

    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    invoice_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    xero_invoice_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
    )

    period_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    period_end: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
        server_default="USD",
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        server_default="draft",
        index=True,
    )

    customer: Mapped["Customer"] = relationship()

    line_items: Mapped[list["InvoiceLineItem"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )