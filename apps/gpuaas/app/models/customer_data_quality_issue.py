from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.gpuaas.app.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from apps.gpuaas.app.models.customer import Customer


class CustomerDataQualityIssue(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "customer_data_quality_issues"

    __table_args__ = (
        UniqueConstraint(
            "issue_type",
            "source",
            "entity_type",
            "external_id",
            name="uq_customer_dq_issue_identity",
        ),
    )

    customer_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    issue_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="open",
    )

    details: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    customer: Mapped["Customer | None"] = relationship()
