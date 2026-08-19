from dataclasses import dataclass
from typing import Any

from apps.gpuaas.app.repositories.customer_identity import (
    CustomerIdentityRepository,
)


@dataclass(frozen=True)
class OrphanRecord:
    source: str
    entity_type: str
    external_id: str


class CustomerOrphanDetectionService:
    def __init__(
        self,
        *,
        identity_repository: CustomerIdentityRepository,
    ) -> None:
        self.identities = identity_repository

    async def check_record(
        self,
        *,
        source: str,
        entity_type: str,
        external_id: str,
    ) -> OrphanRecord | None:
        identity = (
            await self.identities.find_by_external_identity(
                source=source,
                entity_type=entity_type,
                external_id=external_id,
            )
        )

        if identity is not None:
            return None

        return OrphanRecord(
            source=source,
            entity_type=entity_type,
            external_id=external_id,
        )

    async def check_records(
        self,
        records: list[dict[str, Any]],
    ) -> list[OrphanRecord]:
        orphaned: list[OrphanRecord] = []

        for record in records:
            result = await self.check_record(
                source=record["source"],
                entity_type=record["entity_type"],
                external_id=str(record["external_id"]),
            )

            if result is not None:
                orphaned.append(result)

        return orphaned
