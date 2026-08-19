from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.gpuaas.app.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from apps.gpuaas.app.models.customer import Customer


class CustomerIdentity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customer_identities"

    __table_args__ = (
        UniqueConstraint(
            "source",
            "entity_type",
            "external_id",
            name="uq_customer_identity_source_entity_external",
        ),
        UniqueConstraint(
            "customer_id",
            "source",
            "entity_type",
            name="uq_customer_identity_customer_source_entity",
        ),
    )

    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"),
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

    customer: Mapped["Customer"] = relationship(
        back_populates="identities",
    )
