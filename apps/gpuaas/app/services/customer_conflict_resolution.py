from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID

from apps.gpuaas.app.models.customer_data_quality_audit import (
    CustomerDataQualityAudit,
)
from apps.gpuaas.app.repositories.customer_data_quality_audit import (
    CustomerDataQualityAuditRepository,
)
from apps.gpuaas.app.services.customer_field_ownership import (
    CustomerFieldOwnershipPolicy,
    OwnershipDecision,
)


class ConflictResolutionDecision(StrEnum):
    SOURCE_WINS = "source_wins"
    CANONICAL_WINS = "canonical_wins"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class ConflictResolutionResult:
    decision: ConflictResolutionDecision
    ownership: OwnershipDecision
    value: Any


class CustomerConflictResolutionService:
    def __init__(
        self,
        *,
        audit_repository: CustomerDataQualityAuditRepository,
    ) -> None:
        self.audit_repository = audit_repository

    async def resolve(
        self,
        *,
        customer_id: UUID,
        source: str,
        entity_type: str,
        external_id: str,
        field: str,
        canonical_value: Any,
        source_value: Any,
        policy: CustomerFieldOwnershipPolicy,
    ) -> ConflictResolutionResult:
        ownership = policy.decide(
            field=field,
            source=source,
        )

        if ownership == OwnershipDecision.AUTHORITATIVE:
            decision = (
                ConflictResolutionDecision.SOURCE_WINS
            )
            resolved_value = source_value

        elif ownership == OwnershipDecision.NON_AUTHORITATIVE:
            decision = (
                ConflictResolutionDecision.CANONICAL_WINS
            )
            resolved_value = canonical_value

        else:
            decision = (
                ConflictResolutionDecision.UNRESOLVED
            )
            resolved_value = canonical_value

        audit = CustomerDataQualityAudit(
            customer_id=customer_id,
            source=source,
            entity_type=entity_type,
            external_id=external_id,
            field=field,
            decision=decision.value,
            ownership=ownership.value,
            canonical_value=canonical_value,
            source_value=source_value,
            resolved_value=resolved_value,
            resolved_at=datetime.now(timezone.utc),
        )

        await self.audit_repository.create(audit)

        return ConflictResolutionResult(
            decision=decision,
            ownership=ownership,
            value=resolved_value,
        )
