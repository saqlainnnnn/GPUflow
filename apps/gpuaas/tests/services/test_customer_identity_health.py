from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.models.customer_identity import CustomerIdentity
from apps.gpuaas.app.services.customer_identity_health import (
    CustomerIdentityHealthService,
    IdentityHealthStatus,
)


def build_service():
    repository = AsyncMock()
    service = CustomerIdentityHealthService(repository)

    return service, repository


@pytest.mark.asyncio
async def test_all_expected_identities_are_matched():
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

    result = await service.check_customer(
        customer_id=customer_id,
        expected_identities=[
            ("pipedrive", "organization"),
            ("xero", "contact"),
        ],
    )

    assert result.status is IdentityHealthStatus.MATCHED
    assert result.missing == []
    assert result.matched == [
        ("pipedrive", "organization"),
        ("xero", "contact"),
    ]


@pytest.mark.asyncio
async def test_missing_expected_identity_is_reported():
    service, repository = build_service()

    customer_id = uuid4()

    pipedrive_identity = CustomerIdentity(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="123",
    )

    repository.find_for_customer.return_value = [
        pipedrive_identity,
    ]

    result = await service.check_customer(
        customer_id=customer_id,
        expected_identities=[
            ("pipedrive", "organization"),
            ("xero", "contact"),
        ],
    )

    assert result.status is IdentityHealthStatus.MISSING
    assert result.matched == [
        ("pipedrive", "organization"),
    ]
    assert result.missing == [
        ("xero", "contact"),
    ]


@pytest.mark.asyncio
async def test_customer_with_no_identities_is_missing_all_expected_identities():
    service, repository = build_service()

    customer_id = uuid4()

    repository.find_for_customer.return_value = []

    result = await service.check_customer(
        customer_id=customer_id,
        expected_identities=[
            ("pipedrive", "organization"),
            ("xero", "contact"),
        ],
    )

    assert result.status is IdentityHealthStatus.MISSING
    assert result.matched == []
    assert result.missing == [
        ("pipedrive", "organization"),
        ("xero", "contact"),
    ]


@pytest.mark.asyncio
async def test_no_expected_identities_is_matched():
    service, repository = build_service()

    customer_id = uuid4()

    repository.find_for_customer.return_value = []

    result = await service.check_customer(
        customer_id=customer_id,
        expected_identities=[],
    )

    assert result.status is IdentityHealthStatus.MATCHED
    assert result.matched == []
    assert result.missing == []
