from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.models.customer_identity import CustomerIdentity
from apps.gpuaas.app.services.customer_identity import (
    CustomerIdentityService,
)


def build_service():
    repository = AsyncMock()
    service = CustomerIdentityService(repository)

    return service, repository


@pytest.mark.asyncio
async def test_link_identity_creates_when_identity_does_not_exist():
    service, repository = build_service()

    customer_id = uuid4()

    repository.find_by_external_identity.return_value = None

    created_identity = CustomerIdentity(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    repository.create.return_value = created_identity

    result = await service.link_identity(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    assert result is created_identity

    repository.find_by_external_identity.assert_awaited_once_with(
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    repository.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_link_identity_is_idempotent_for_same_customer():
    service, repository = build_service()

    customer_id = uuid4()

    existing_identity = CustomerIdentity(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    repository.find_by_external_identity.return_value = existing_identity

    result = await service.link_identity(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    assert result is existing_identity
    repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_link_identity_rejects_identity_owned_by_another_customer():
    service, repository = build_service()

    existing_customer_id = uuid4()
    requested_customer_id = uuid4()

    existing_identity = CustomerIdentity(
        customer_id=existing_customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    repository.find_by_external_identity.return_value = existing_identity

    with pytest.raises(ValueError, match="already linked"):
        await service.link_identity(
            customer_id=requested_customer_id,
            source="pipedrive",
            entity_type="organization",
            external_id="12345",
        )

    repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_identity_returns_repository_result():
    service, repository = build_service()

    identity = CustomerIdentity(
        customer_id=uuid4(),
        source="xero",
        entity_type="contact",
        external_id="xero-123",
    )

    repository.find_by_external_identity.return_value = identity

    result = await service.get_identity(
        source="xero",
        entity_type="contact",
        external_id="xero-123",
    )

    assert result is identity
