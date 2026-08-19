from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from apps.gpuaas.app.models.customer import Customer
from apps.gpuaas.app.models.xero_connection import XeroConnection
from apps.gpuaas.app.services.xero_reconciliation_service import (
    XeroReconciliationService,
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


def build_connection(customer_id):
    return XeroConnection(
        customer_id=customer_id,
        tenant_id="tenant-123",
        tenant_name="Acme Xero",
        xero_contact_id="contact-123",
        access_token="access-token",
        refresh_token="refresh-token",
        expires_at=None,
    )


@pytest.mark.asyncio
async def test_reconcile_xero_contact():
    customer = build_customer()
    connection = build_connection(customer.id)

    session = AsyncMock()

    customer_repository = AsyncMock()
    customer_repository.get_by_id.return_value = customer

    identity_repository = AsyncMock()

    identity = MagicMock()
    identity.customer_id = customer.id
    identity.source = "xero"
    identity.entity_type = "contact"
    identity.external_id = "contact-123"

    identity_repository.find_by_external_identity.return_value = identity

    xero_client = MagicMock()

    xero_client.get_contact = AsyncMock(
        return_value={
            "ContactID": "contact-123",
            "Name": "ACME AI",
            "EmailAddress": "HELLO@ACME.AI",
            "Country": "in",
        }
    )

    service = XeroReconciliationService(
        session=session,
        customer_repository=customer_repository,
        identity_repository=identity_repository,
    )

    with (
        patch(
            "apps.gpuaas.app.services.xero_reconciliation_service"
            ".get_valid_connection",
            new=AsyncMock(return_value=connection),
        ),
        patch(
            "apps.gpuaas.app.services.xero_reconciliation_service"
            ".XeroClient",
            return_value=xero_client,
        ),
    ):
        result = await service.reconcile_contact(
            customer_id=customer.id,
            contact_id="contact-123",
        )

    assert result.source == "xero"
    assert result.entity_type == "contact"
    assert result.status.value == "matched"
    assert result.mismatches == []
    assert result.missing == []

    identity_repository.find_by_external_identity.assert_awaited_once_with(
        source="xero",
        entity_type="contact",
        external_id="contact-123",
    )

    xero_client.get_contact.assert_awaited_once_with(
        "contact-123",
    )


@pytest.mark.asyncio
async def test_reconcile_xero_contact_reports_mismatch():
    customer = build_customer()
    connection = build_connection(customer.id)

    session = AsyncMock()

    customer_repository = AsyncMock()
    customer_repository.get_by_id.return_value = customer

    identity_repository = AsyncMock()

    identity = MagicMock()
    identity.customer_id = customer.id

    identity_repository.find_by_external_identity.return_value = identity

    xero_client = MagicMock()

    xero_client.get_contact = AsyncMock(
        return_value={
            "ContactID": "contact-123",
            "Name": "Acme Compute",
            "EmailAddress": "HELLO@ACME.AI",
            "Country": "in",
        }
    )

    service = XeroReconciliationService(
        session=session,
        customer_repository=customer_repository,
        identity_repository=identity_repository,
    )

    with (
        patch(
            "apps.gpuaas.app.services.xero_reconciliation_service"
            ".get_valid_connection",
            new=AsyncMock(return_value=connection),
        ),
        patch(
            "apps.gpuaas.app.services.xero_reconciliation_service"
            ".XeroClient",
            return_value=xero_client,
        ),
    ):
        result = await service.reconcile_contact(
            customer_id=customer.id,
            contact_id="contact-123",
        )

    assert result.status.value == "mismatch"
    assert result.mismatches == ["company_name"]


@pytest.mark.asyncio
async def test_reconcile_xero_contact_rejects_unlinked_identity():
    customer = build_customer()
    connection = build_connection(customer.id)

    session = AsyncMock()

    customer_repository = AsyncMock()
    customer_repository.get_by_id.return_value = customer

    identity_repository = AsyncMock()
    identity_repository.find_by_external_identity.return_value = None

    service = XeroReconciliationService(
        session=session,
        customer_repository=customer_repository,
        identity_repository=identity_repository,
    )

    with patch(
        "apps.gpuaas.app.services.xero_reconciliation_service"
        ".get_valid_connection",
        new=AsyncMock(return_value=connection),
    ):
        with pytest.raises(
            ValueError,
            match="identity is not linked",
        ):
            await service.reconcile_contact(
                customer_id=customer.id,
                contact_id="contact-123",
            )
