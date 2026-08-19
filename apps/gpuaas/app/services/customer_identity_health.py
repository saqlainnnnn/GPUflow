from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from apps.gpuaas.app.models.customer_identity import CustomerIdentity
from apps.gpuaas.app.repositories.customer_identity import (
    CustomerIdentityRepository,
)


class IdentityHealthStatus(StrEnum):
    MATCHED = "matched"
    MISSING = "missing"


IdentityKey = tuple[str, str]


@dataclass(frozen=True)
class CustomerIdentityHealth:
    customer_id: UUID
    status: IdentityHealthStatus
    matched: list[IdentityKey]
    missing: list[IdentityKey]


class CustomerIdentityHealthService:
    def __init__(
        self,
        repository: CustomerIdentityRepository,
    ) -> None:
        self.repository = repository

    async def check_customer(
        self,
        *,
        customer_id: UUID,
        expected_identities: list[IdentityKey],
    ) -> CustomerIdentityHealth:
        identities = await self.repository.find_for_customer(
            customer_id
        )

        existing = {
            (identity.source, identity.entity_type)
            for identity in identities
        }

        matched = [
            identity_key
            for identity_key in expected_identities
            if identity_key in existing
        ]

        missing = [
            identity_key
            for identity_key in expected_identities
            if identity_key not in existing
        ]

        status = (
            IdentityHealthStatus.MATCHED
            if not missing
            else IdentityHealthStatus.MISSING
        )

        return CustomerIdentityHealth(
            customer_id=customer_id,
            status=status,
            matched=matched,
            missing=missing,
        )
