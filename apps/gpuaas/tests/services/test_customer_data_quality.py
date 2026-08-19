from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.models.customer_identity import CustomerIdentity
from apps.gpuaas.app.services.customer_data_quality import (
    CustomerDataQualityStatus,
    CustomerDataQualityService,
)


def build_service():
    identity_repository = AsyncMock()

    service = CustomerDataQualityService(
        identity_repository=identity_repository,
    )

    return service, identity_repository


@pytest.mark.asyncio
async def test_all_sources_healthy():
    service, repository = build_service()

    customer_id = uuid4()

    pipedrive_identity = CustomerIdentity(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="123",
    )

    xero_identity = CustomerIdentity(
        customer_id=customer_id,
        source="xero",
        entity_type="contact",
        external_id="456",
    )

    repository.find_for_customer.return_value = [
        pipedrive_identity,
        xero_identity,
    ]

    reconciler = AsyncMock()

    pipedrive_result = MagicMock()
    pipedrive_result.source = "pipedrive"
    pipedrive_result.entity_type = "organization"
    pipedrive_result.status.value = "matched"
    pipedrive_result.mismatches = []
    pipedrive_result.missing = []

    xero_result = MagicMock()
    xero_result.source = "xero"
    xero_result.entity_type = "contact"
    xero_result.status.value = "matched"
    xero_result.mismatches = []
    xero_result.missing = []

    reconciler.side_effect = [
        pipedrive_result,
        xero_result,
    ]

    result = await service.build_report(
        customer_id=customer_id,
        reconciler=reconciler,
    )

    assert result.status is CustomerDataQualityStatus.HEALTHY
    assert len(result.sources) == 2
    assert result.sources[0].status == "matched"
    assert result.sources[1].status == "matched"


@pytest.mark.asyncio
async def test_any_mismatch_makes_customer_report_mismatch():
    service, repository = build_service()

    customer_id = uuid4()

    repository.find_for_customer.return_value = [
        CustomerIdentity(
            customer_id=customer_id,
            source="pipedrive",
            entity_type="organization",
            external_id="123",
        ),
        CustomerIdentity(
            customer_id=customer_id,
            source="xero",
            entity_type="contact",
            external_id="456",
        ),
    ]

    reconciler = AsyncMock()

    healthy = MagicMock()
    healthy.source = "pipedrive"
    healthy.entity_type = "organization"
    healthy.status.value = "matched"
    healthy.mismatches = []
    healthy.missing = []

    mismatch = MagicMock()
    mismatch.source = "xero"
    mismatch.entity_type = "contact"
    mismatch.status.value = "mismatch"
    mismatch.mismatches = ["company_name"]
    mismatch.missing = []

    reconciler.side_effect = [healthy, mismatch]

    result = await service.build_report(
        customer_id=customer_id,
        reconciler=reconciler,
    )

    assert result.status is CustomerDataQualityStatus.MISMATCH


@pytest.mark.asyncio
async def test_incomplete_without_mismatch_is_incomplete():
    service, repository = build_service()

    customer_id = uuid4()

    repository.find_for_customer.return_value = [
        CustomerIdentity(
            customer_id=customer_id,
            source="pipedrive",
            entity_type="organization",
            external_id="123",
        )
    ]

    reconciler = AsyncMock()

    incomplete = MagicMock()
    incomplete.source = "pipedrive"
    incomplete.entity_type = "organization"
    incomplete.status.value = "incomplete"
    incomplete.mismatches = []
    incomplete.missing = ["email"]

    reconciler.return_value = incomplete

    result = await service.build_report(
        customer_id=customer_id,
        reconciler=reconciler,
    )

    assert result.status is CustomerDataQualityStatus.INCOMPLETE


@pytest.mark.asyncio
async def test_no_identities_is_unverified():
    service, repository = build_service()

    customer_id = uuid4()

    repository.find_for_customer.return_value = []

    reconciler = AsyncMock()

    result = await service.build_report(
        customer_id=customer_id,
        reconciler=reconciler,
    )

    assert result.status is CustomerDataQualityStatus.UNVERIFIED
    assert result.sources == []
    reconciler.assert_not_awaited()
