from typing import Any, Protocol
from uuid import UUID

from apps.gpuaas.app.models.customer import Customer
from apps.gpuaas.app.repositories.customer import CustomerRepository
from apps.gpuaas.app.repositories.customer_identity import (
    CustomerIdentityRepository,
)
from apps.gpuaas.app.services.customer_reconciliation import (
    CustomerSourceReconciliation,
    reconcile_customer_source,
)


class CustomerSourceAdapter(Protocol):
    def to_customer_record(
        self,
        source_record: dict[str, Any],
    ) -> dict[str, str | None]:
        ...


class CustomerReconciliationService:
    def __init__(
        self,
        *,
        customer_repository: CustomerRepository,
        identity_repository: CustomerIdentityRepository,
    ) -> None:
        self.customers = customer_repository
        self.identities = identity_repository

    async def reconcile_identity(
        self,
        *,
        customer_id: UUID,
        source: str,
        entity_type: str,
        external_id: str,
        source_record: dict[str, Any],
        adapter: CustomerSourceAdapter,
    ) -> CustomerSourceReconciliation:
        customer: Customer | None = await self.customers.get_by_id(
            customer_id
        )

        if customer is None:
            raise ValueError(
                f"Customer '{customer_id}' not found"
            )

        identity = (
            await self.identities.find_by_external_identity(
                source=source,
                entity_type=entity_type,
                external_id=external_id,
            )
        )

        if identity is None:
            raise ValueError(
                "Customer identity is not linked"
            )

        if identity.customer_id != customer_id:
            raise ValueError(
                "Customer identity belongs to another customer"
            )

        adapted_record = adapter.to_customer_record(
            source_record
        )

        return reconcile_customer_source(
            customer=customer,
            source=source,
            entity_type=entity_type,
            source_record=adapted_record,
        )
