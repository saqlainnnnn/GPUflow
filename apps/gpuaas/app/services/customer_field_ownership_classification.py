from dataclasses import dataclass
from enum import StrEnum

from apps.gpuaas.app.services.customer_field_ownership import (
    CustomerFieldOwnershipPolicy,
    OwnershipDecision,
)
from apps.gpuaas.app.services.customer_reconciliation import (
    FieldReconciliation,
    FieldReconciliationStatus,
)


class FieldOwnershipClassification(StrEnum):
    AUTHORITATIVE_MISMATCH = "authoritative_mismatch"
    NON_AUTHORITATIVE_MISMATCH = "non_authoritative_mismatch"
    MISSING_AUTHORITATIVE = "missing_authoritative"
    MISSING_NON_AUTHORITATIVE = "missing_non_authoritative"


@dataclass(frozen=True)
class ClassifiedFieldReconciliation:
    field: str
    status: FieldReconciliationStatus
    canonical_value: str | None
    source_value: str | None
    ownership: OwnershipDecision
    classification: FieldOwnershipClassification | None


def classify_reconciliation_fields(
    *,
    fields: dict[str, FieldReconciliation],
    source: str,
    policy: CustomerFieldOwnershipPolicy,
) -> dict[str, ClassifiedFieldReconciliation]:
    result: dict[str, ClassifiedFieldReconciliation] = {}

    for field_name, field_result in fields.items():
        ownership = policy.decide(
            field=field_name,
            source=source,
        )

        classification = None

        if field_result.status is FieldReconciliationStatus.MISMATCH:
            if ownership is OwnershipDecision.AUTHORITATIVE:
                classification = (
                    FieldOwnershipClassification.AUTHORITATIVE_MISMATCH
                )
            elif ownership is OwnershipDecision.NON_AUTHORITATIVE:
                classification = (
                    FieldOwnershipClassification.NON_AUTHORITATIVE_MISMATCH
                )

        elif field_result.status in {
            FieldReconciliationStatus.MISSING_ON_SOURCE,
            FieldReconciliationStatus.MISSING_ON_CANONICAL,
        }:
            if ownership is OwnershipDecision.AUTHORITATIVE:
                classification = (
                    FieldOwnershipClassification.MISSING_AUTHORITATIVE
                )
            elif ownership is OwnershipDecision.NON_AUTHORITATIVE:
                classification = (
                    FieldOwnershipClassification.MISSING_NON_AUTHORITATIVE
                )

        result[field_name] = ClassifiedFieldReconciliation(
            field=field_name,
            status=field_result.status,
            canonical_value=field_result.canonical_value,
            source_value=field_result.source_value,
            ownership=ownership,
            classification=classification,
        )

    return result
