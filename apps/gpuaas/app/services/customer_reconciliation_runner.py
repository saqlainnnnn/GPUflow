from dataclasses import replace
from typing import Any
from uuid import UUID

from apps.gpuaas.app.services.customer_conflict_resolution import (
    CustomerConflictResolutionService,
)
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
        conflict_resolution: CustomerConflictResolutionService | None = None,
    ) -> None:
        self.reconciler = reconciler
        self.persistence = persistence
        self.conflict_resolution = conflict_resolution

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
            classified = (
                reconciliation.classify_ownership(
                    policy=ownership_policy
                )
            )

            resolved_fields = dict(classified)

            if self.conflict_resolution is not None:
                for field_name in (
                    reconciliation.mismatches
                ):
                    field_result = classified.get(
                        field_name
                    )

                    if field_result is None:
                        continue

                    resolution = (
                        await self.conflict_resolution.resolve(
                            customer_id=customer_id,
                            source=source,
                            entity_type=entity_type,
                            external_id=external_id,
                            field=field_name,
                            canonical_value=(
                                field_result.canonical_value
                            ),
                            source_value=(
                                field_result.source_value
                            ),
                            policy=ownership_policy,
                        )
                    )

                    resolved_fields[
                        field_name
                    ] = replace(
                        field_result,
                        canonical_value=(
                            resolution.value
                        ),
                        source_value=(
                            field_result.source_value
                        ),
                    )

            persistence_reconciliation = replace(
                reconciliation,
                fields=resolved_fields,
            )

        record = await self.persistence.persist(
            customer_id=customer_id,
            external_id=external_id,
            reconciliation=persistence_reconciliation,
        )

        return reconciliation, record
