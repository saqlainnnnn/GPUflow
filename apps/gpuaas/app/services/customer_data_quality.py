from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from apps.gpuaas.app.models.customer_identity import CustomerIdentity
from apps.gpuaas.app.repositories.customer_identity import (
    CustomerIdentityRepository,
)


class CustomerDataQualityStatus(StrEnum):
    HEALTHY = "healthy"
    INCOMPLETE = "incomplete"
    MISMATCH = "mismatch"
    UNVERIFIED = "unverified"


class ReconciliationResult(Protocol):
    source: str
    entity_type: str
    status: object
    mismatches: list[str]
    missing: list[str]


@dataclass(frozen=True)
class SourceDataQuality:
    source: str
    entity_type: str
    external_id: str
    status: str
    mismatches: list[str]
    missing: list[str]


@dataclass(frozen=True)
class CustomerDataQuality:
    customer_id: UUID
    status: CustomerDataQualityStatus
    sources: list[SourceDataQuality]


class CustomerDataQualityService:
    def __init__(
        self,
        *,
        identity_repository: CustomerIdentityRepository,
    ) -> None:
        self.identities = identity_repository

    async def build_report(
        self,
        *,
        customer_id: UUID,
        reconciler,
    ) -> CustomerDataQuality:
        identities: list[CustomerIdentity] = (
            await self.identities.find_for_customer(
                customer_id
            )
        )

        if not identities:
            return CustomerDataQuality(
                customer_id=customer_id,
                status=CustomerDataQualityStatus.UNVERIFIED,
                sources=[],
            )

        source_results: list[SourceDataQuality] = []

        for identity in identities:
            result: ReconciliationResult = await reconciler(
                identity
            )

            source_results.append(
                SourceDataQuality(
                    source=result.source,
                    entity_type=result.entity_type,
                    external_id=identity.external_id,
                    status=result.status.value,
                    mismatches=list(result.mismatches),
                    missing=list(result.missing),
                )
            )

        if any(
            source.status == "mismatch"
            for source in source_results
        ):
            overall_status = CustomerDataQualityStatus.MISMATCH

        elif any(
            source.status == "incomplete"
            for source in source_results
        ):
            overall_status = CustomerDataQualityStatus.INCOMPLETE

        else:
            overall_status = CustomerDataQualityStatus.HEALTHY

        return CustomerDataQuality(
            customer_id=customer_id,
            status=overall_status,
            sources=source_results,
        )
