from datetime import datetime, timezone
from uuid import UUID

from apps.gpuaas.app.models.customer_data_quality import (
    CustomerDataQualityRecord,
)
from apps.gpuaas.app.repositories.customer_data_quality import (
    CustomerDataQualityRepository,
)


def _serialize_status(status) -> str:
    if hasattr(status, "value"):
        return status.value

    return str(status)


def _serialize_field_result(field_result) -> dict:
    if isinstance(field_result, dict):
        status = field_result.get("status")
        canonical_value = field_result.get(
            "canonical_value"
        )
        source_value = field_result.get(
            "source_value"
        )
        ownership = field_result.get("ownership")
        classification = field_result.get(
            "classification"
        )

    else:
        status = field_result.status
        canonical_value = field_result.canonical_value
        source_value = field_result.source_value
        ownership = getattr(
            field_result,
            "ownership",
            None,
        )
        classification = getattr(
            field_result,
            "classification",
            None,
        )

    serialized = {
        "status": _serialize_status(status),
        "canonical_value": canonical_value,
        "source_value": source_value,
    }

    if ownership is not None:
        serialized["ownership"] = _serialize_status(
            ownership
        )

    if classification is not None:
        serialized["classification"] = _serialize_status(
            classification
        )

    return serialized


def _serialize_fields(fields: dict) -> dict:
    return {
        field_name: _serialize_field_result(field_result)
        for field_name, field_result in fields.items()
    }


class CustomerDataQualityPersistenceService:
    def __init__(
        self,
        *,
        repository: CustomerDataQualityRepository,
    ) -> None:
        self.repository = repository

    async def persist(
        self,
        *,
        customer_id: UUID,
        external_id: str,
        reconciliation,
    ) -> CustomerDataQualityRecord:
        checked_at = datetime.now(timezone.utc)

        serialized_fields = _serialize_fields(
            reconciliation.fields
        )

        existing = await self.repository.find_for_identity(
            customer_id=customer_id,
            source=reconciliation.source,
            entity_type=reconciliation.entity_type,
            external_id=external_id,
        )

        if existing is not None:
            existing.status = reconciliation.status.value
            existing.mismatches = list(
                reconciliation.mismatches
            )
            existing.missing = list(
                reconciliation.missing
            )
            existing.fields = serialized_fields
            existing.checked_at = checked_at

            await self.repository.session.flush()
            await self.repository.session.refresh(existing)

            return existing

        record = CustomerDataQualityRecord(
            customer_id=customer_id,
            source=reconciliation.source,
            entity_type=reconciliation.entity_type,
            external_id=external_id,
            status=reconciliation.status.value,
            mismatches=list(
                reconciliation.mismatches
            ),
            missing=list(
                reconciliation.missing
            ),
            fields=serialized_fields,
            checked_at=checked_at,
        )

        return await self.repository.create(record)
