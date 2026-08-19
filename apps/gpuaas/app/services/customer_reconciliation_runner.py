from typing import Any
from uuid import UUID

from apps.gpuaas.app.services.customer_data_quality_persistence import (
    CustomerDataQualityPersistenceService,
)
from apps.gpuaas.app.services.customer_reconciliation_service import (
    CustomerReconciliationService,
)


class CustomerReconciliationRunner:
    def __init__(
        self,
        *,
        reconciler: CustomerReconciliationService,
        persistence: CustomerDataQualityPersistenceService,
    ) -> None:
        self.reconciler = reconciler
        self.persistence = persistence

    async def reconcile_and_persist(
        self,
        *,
        customer_id: UUID,
        source: str,
        entity_type: str,
        external_id: str,
        source_record: dict[str, Any],
        adapter,
        ownership_policy=None,
    ):
        reconciliation = await self.reconciler.reconcile_identity(
            customer_id=customer_id,
            source=source,
            entity_type=entity_type,
            external_id=external_id,
            source_record=source_record,
            adapter=adapter,
        )

        persistence_reconciliation = reconciliation

        if ownership_policy is not None:
            from dataclasses import replace

            classified = (
                reconciliation.classify_ownership(
                    policy=ownership_policy
                )
            )

            persistence_reconciliation = replace(
                reconciliation,
                fields=classified,
            )

        record = await self.persistence.persist(
            customer_id=customer_id,
            external_id=external_id,
            reconciliation=persistence_reconciliation,
        )

        return reconciliation, record
