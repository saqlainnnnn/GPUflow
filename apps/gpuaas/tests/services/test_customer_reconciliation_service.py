from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.models.customer import Customer
from apps.gpuaas.app.models.customer_identity import CustomerIdentity
from apps.gpuaas.app.services.customer_reconciliation_service import (
    CustomerReconciliationService,
)


def build_customer():
    return Customer(
        id=uuid4(),
        external_id=f"customer-{uuid4()}",
        company_name="Acme AI",
        email="hello@acme.ai",
        country="IN",
        status="active",
    )


def build_identity(customer_id):
    return CustomerIdentity(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )


def build_service():
    repository = AsyncMock()
    service = CustomerReconciliationService(
        customer_repository=repository,
        identity_repository=repository,
    )

    return service, repository


@pytest.mark.asyncio
async def test_reconcile_identity_adapts_and_reconciles_source_record():
    customer = build_customer()
    identity = build_identity(customer.id)

    service, repository = build_service()

    repository.get_by_id.return_value = customer
    repository.find_by_external_identity.return_value = identity

    adapter = MagicMock()
    adapter.to_customer_record.return_value = {
        "company_name": "ACME AI",
        "email": "HELLO@ACME.AI",
        "country": "in",
    }

    result = await service.reconcile_identity(
        customer_id=customer.id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        source_record={
            "name": "ACME AI",
            "email": "HELLO@ACME.AI",
            "country": "in",
        },
        adapter=adapter,
    )

    assert result.source == "pipedrive"
    assert result.entity_type == "organization"
    assert result.status.value == "matched"
    assert result.mismatches == []
    assert result.missing == []

    adapter.to_customer_record.assert_called_once_with(
        {
            "name": "ACME AI",
            "email": "HELLO@ACME.AI",
            "country": "in",
        }
    )


@pytest.mark.asyncio
async def test_reconcile_identity_reports_mismatch():
    customer = build_customer()
    identity = build_identity(customer.id)

    service, repository = build_service()

    repository.get_by_id.return_value = customer
    repository.find_by_external_identity.return_value = identity

    adapter = MagicMock()
    adapter.to_customer_record.return_value = {
        "company_name": "Acme Compute",
        "email": "hello@acme.ai",
        "country": "IN",
    }

    result = await service.reconcile_identity(
        customer_id=customer.id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        source_record={},
        adapter=adapter,
    )

    assert result.status.value == "mismatch"
    assert result.mismatches == ["company_name"]


@pytest.mark.asyncio
async def test_reconcile_identity_rejects_missing_customer():
    service, repository = build_service()

    customer_id = uuid4()

    repository.get_by_id.return_value = None

    adapter = MagicMock()

    with pytest.raises(
        ValueError,
        match="Customer .* not found",
    ):
        await service.reconcile_identity(
            customer_id=customer_id,
            source="pipedrive",
            entity_type="organization",
            external_id="12345",
            source_record={},
            adapter=adapter,
        )

    adapter.to_customer_record.assert_not_called()


@pytest.mark.asyncio
async def test_reconcile_identity_rejects_unlinked_identity():
    customer = build_customer()

    service, repository = build_service()

    repository.get_by_id.return_value = customer
    repository.find_by_external_identity.return_value = None

    adapter = MagicMock()

    with pytest.raises(
        ValueError,
        match="identity is not linked",
    ):
        await service.reconcile_identity(
            customer_id=customer.id,
            source="pipedrive",
            entity_type="organization",
            external_id="12345",
            source_record={},
            adapter=adapter,
        )

    adapter.to_customer_record.assert_not_called()
