from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.gpuaas.app.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    pass


class CustomerReconciliationRun(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "customer_reconciliation_runs"

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    processed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    succeeded: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    failed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
