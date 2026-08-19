from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.services.customer_conflict_resolution import (
    ConflictResolutionDecision,
    CustomerConflictResolutionService,
)
from apps.gpuaas.app.services.customer_field_ownership import (
    CustomerFieldOwnershipPolicy,
    OwnershipDecision,
)


def build_service():
    audit_repository = AsyncMock()

    service = CustomerConflictResolutionService(
        audit_repository=audit_repository,
    )

    return service, audit_repository


@pytest.mark.asyncio
async def test_authoritative_source_wins():
    service, audit_repository = build_service()

    customer_id = uuid4()

    policy = CustomerFieldOwnershipPolicy(
        {
            "company_name": "pipedrive",
        }
    )

    result = await service.resolve(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        field="company_name",
        canonical_value="Acme AI",
        source_value="Acme Compute",
        policy=policy,
    )

    assert result.decision == (
        ConflictResolutionDecision.SOURCE_WINS
    )
    assert result.ownership == (
        OwnershipDecision.AUTHORITATIVE
    )
    assert result.value == "Acme Compute"

    audit_repository.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_non_authoritative_source_preserves_canonical():
    service, audit_repository = build_service()

    customer_id = uuid4()

    policy = CustomerFieldOwnershipPolicy(
        {
            "company_name": "pipedrive",
        }
    )

    result = await service.resolve(
        customer_id=customer_id,
        source="xero",
        entity_type="contact",
        external_id="contact-123",
        field="company_name",
        canonical_value="Acme AI",
        source_value="Acme Compute",
        policy=policy,
    )

    assert result.decision == (
        ConflictResolutionDecision.CANONICAL_WINS
    )
    assert result.ownership == (
        OwnershipDecision.NON_AUTHORITATIVE
    )
    assert result.value == "Acme AI"

    audit_repository.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_unknown_ownership_does_not_overwrite():
    service, audit_repository = build_service()

    customer_id = uuid4()

    policy = CustomerFieldOwnershipPolicy({})

    result = await service.resolve(
        customer_id=customer_id,
        source="unknown",
        entity_type="organization",
        external_id="12345",
        field="company_name",
        canonical_value="Acme AI",
        source_value="Acme Compute",
        policy=policy,
    )

    assert result.decision == (
        ConflictResolutionDecision.UNRESOLVED
    )
    assert result.ownership == (
        OwnershipDecision.UNKNOWN
    )
    assert result.value == "Acme AI"

    audit_repository.create.assert_awaited_once()
