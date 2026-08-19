from uuid import UUID

from apps.gpuaas.app.models.customer_identity import CustomerIdentity
from apps.gpuaas.app.repositories.customer_identity import (
    CustomerIdentityRepository,
)


class CustomerIdentityService:
    def __init__(
        self,
        repository: CustomerIdentityRepository,
    ) -> None:
        self.repository = repository

    async def get_identity(
        self,
        *,
        source: str,
        entity_type: str,
        external_id: str,
    ) -> CustomerIdentity | None:
        return await self.repository.find_by_external_identity(
            source=source,
            entity_type=entity_type,
            external_id=external_id,
        )

    async def link_identity(
        self,
        *,
        customer_id: UUID,
        source: str,
        entity_type: str,
        external_id: str,
    ) -> CustomerIdentity:
        existing = await self.repository.find_by_external_identity(
            source=source,
            entity_type=entity_type,
            external_id=external_id,
        )

        if existing is not None:
            if existing.customer_id != customer_id:
                raise ValueError(
                    "External identity is already linked to another customer"
                )

            return existing

        identity = CustomerIdentity(
            customer_id=customer_id,
            source=source,
            entity_type=entity_type,
            external_id=external_id,
        )

        return await self.repository.create(identity)
