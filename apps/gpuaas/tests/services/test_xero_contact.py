from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from apps.gpuaas.app.models.customer import Customer
from apps.gpuaas.app.models.xero_connection import XeroConnection
from apps.gpuaas.app.services.xero_contact import XeroContactService


def build_customer():
    return Customer(
        id=uuid4(),
        external_id=f"customer-{uuid4()}",
        company_name="Acme AI",
        email="billing@acme.ai",
        country="IN",
        status="active",
    )


def build_connection(
    customer_id,
    contact_id=None,
):
    return XeroConnection(
        customer_id=customer_id,
        tenant_id="tenant-123",
        tenant_name="Acme Xero",
        xero_contact_id=contact_id,
        access_token="access-token",
        refresh_token="refresh-token",
        expires_at=None,
    )


@pytest.mark.asyncio
async def test_existing_xero_contact_is_linked_to_customer_identity():
    customer = build_customer()
    connection = build_connection(
        customer.id,
        contact_id="contact-123",
    )

    session = AsyncMock()

    customers = AsyncMock()
    customers.get_by_id.return_value = customer

    connections = AsyncMock()
    identities = AsyncMock()

    service = XeroContactService(session)

    service.customers = customers
    service.connections = connections
    service.identities = identities

    with patch(
        "apps.gpuaas.app.services.xero_contact.get_valid_connection",
        new=AsyncMock(return_value=connection),
    ):
        result = await service.get_or_create_contact(customer.id)

    assert result == "contact-123"

    identities.link_identity.assert_awaited_once_with(
        customer_id=customer.id,
        source="xero",
        entity_type="contact",
        external_id="contact-123",
    )


@pytest.mark.asyncio
async def test_new_xero_contact_is_linked_to_customer_identity():
    customer = build_customer()
    connection = build_connection(customer.id)

    session = AsyncMock()

    customers = AsyncMock()
    customers.get_by_id.return_value = customer

    connections = AsyncMock()

    identities = AsyncMock()

    xero_client = MagicMock()
    xero_client.find_contact_by_email = AsyncMock(
        return_value=None,
    )
    xero_client.find_contact_by_name = AsyncMock(
        return_value=None,
    )
    xero_client.create_contact = AsyncMock(
        return_value={
            "Contacts": [
                {
                    "ContactID": "contact-456",
                }
            ]
        }
    )

    service = XeroContactService(session)

    service.customers = customers
    service.connections = connections
    service.identities = identities

    with (
        patch(
            "apps.gpuaas.app.services.xero_contact.get_valid_connection",
            new=AsyncMock(return_value=connection),
        ),
        patch(
            "apps.gpuaas.app.services.xero_contact.XeroClient",
            return_value=xero_client,
        ),
    ):
        result = await service.get_or_create_contact(customer.id)

    assert result == "contact-456"

    connections.set_contact_id.assert_awaited_once_with(
        customer.id,
        "contact-456",
    )

    identities.link_identity.assert_awaited_once_with(
        customer_id=customer.id,
        source="xero",
        entity_type="contact",
        external_id="contact-456",
    )


@pytest.mark.asyncio
async def test_xero_client_get_contact():
    from unittest.mock import MagicMock, patch

    from apps.gpuaas.app.integrations.xero.client import XeroClient

    client = XeroClient(
        access_token="access-token",
        tenant_id="tenant-123",
    )

    response = MagicMock()
    response.is_success = True
    response.json.return_value = {
        "Contacts": [
            {
                "ContactID": "contact-123",
                "Name": "Acme AI",
                "EmailAddress": "hello@acme.ai",
                "Country": "IN",
            }
        ]
    }

    http_client = AsyncMock()
    http_client.get.return_value = response

    context_manager = MagicMock()
    context_manager.__aenter__ = AsyncMock(
        return_value=http_client,
    )
    context_manager.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "apps.gpuaas.app.integrations.xero.client.httpx.AsyncClient",
        return_value=context_manager,
    ):
        result = await client.get_contact("contact-123")

    assert result == {
        "ContactID": "contact-123",
        "Name": "Acme AI",
        "EmailAddress": "hello@acme.ai",
        "Country": "IN",
    }

    http_client.get.assert_awaited_once_with(
        "https://api.xero.com/api.xro/2.0/Contacts/contact-123",
        headers=client._headers(),
    )

    response.is_success is True


@pytest.mark.asyncio
async def test_xero_client_list_contacts():
    from unittest.mock import AsyncMock, MagicMock, patch

    from apps.gpuaas.app.integrations.xero.client import XeroClient

    client = XeroClient(
        access_token="access-token",
        tenant_id="tenant-123",
    )

    response = MagicMock()
    response.is_success = True
    response.json.return_value = {
        "Contacts": [
            {
                "ContactID": "contact-123",
                "Name": "Acme AI",
            },
            {
                "ContactID": "contact-456",
                "Name": "Beta Compute",
            },
        ]
    }

    http_client = AsyncMock()
    http_client.get.return_value = response

    context_manager = MagicMock()
    context_manager.__aenter__ = AsyncMock(
        return_value=http_client,
    )
    context_manager.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "apps.gpuaas.app.integrations.xero.client.httpx.AsyncClient",
        return_value=context_manager,
    ):
        result = await client.list_contacts()

    assert result == [
        {
            "ContactID": "contact-123",
            "Name": "Acme AI",
        },
        {
            "ContactID": "contact-456",
            "Name": "Beta Compute",
        },
    ]

    http_client.get.assert_awaited_once_with(
        "https://api.xero.com/api.xro/2.0/Contacts",
        headers=client._headers(),
    )
