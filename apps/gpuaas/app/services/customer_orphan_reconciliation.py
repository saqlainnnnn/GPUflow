from typing import Any

from apps.gpuaas.app.services.customer_orphan_detection import (
    CustomerOrphanDetectionService,
)
from apps.gpuaas.app.services.customer_orphan_issue import (
    CustomerOrphanIssueService,
)


class CustomerOrphanReconciliationService:
    def __init__(
        self,
        *,
        detector: CustomerOrphanDetectionService,
        issue_service: CustomerOrphanIssueService,
    ) -> None:
        self.detector = detector
        self.issue_service = issue_service

    async def process_record(
        self,
        *,
        source: str,
        entity_type: str,
        external_id: str,
    ):
        orphan = await self.detector.check_record(
            source=source,
            entity_type=entity_type,
            external_id=external_id,
        )

        if orphan is not None:
            return await self.issue_service.open_orphan(
                source=source,
                entity_type=entity_type,
                external_id=external_id,
            )

        return await self.issue_service.resolve_orphan(
            source=source,
            entity_type=entity_type,
            external_id=external_id,
        )

    async def process_records(
        self,
        records: list[dict[str, Any]],
    ) -> list[Any]:
        results: list[Any] = []

        for record in records:
            results.append(
                await self.process_record(
                    source=record["source"],
                    entity_type=record["entity_type"],
                    external_id=str(
                        record["external_id"]
                    ),
                )
            )

        return results
