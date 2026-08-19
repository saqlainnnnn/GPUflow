from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.integration_hub.app.integrations.pipedrive.handlers.organization import (
    PipedriveOrganizationHandler,
)


@pytest.mark.asyncio
async def test_organization_handler_upserts_customer_and_links_identity():
    pipedrive = MagicMock()
    gpuaas = MagicMock()

    pipedrive.get_organization = AsyncMock(
        return_value={
            "id": 12345,
            "name": "Acme AI",
            "email": "hello@acme.ai",
            "country": "IN",
        }
    )

    gpuaas.upsert_customer = AsyncMock(
        return_value={
            "id": "customer-123",
            "external_id": "pipedrive:organization:12345",
            "company_name": "Acme AI",
            "email": "hello@acme.ai",
            "country": "IN",
            "status": "active",
        }
    )

    gpuaas.link_customer_identity = AsyncMock(
        return_value={
            "id": "identity-123",
            "customer_id": "customer-123",
            "source": "pipedrive",
            "entity_type": "organization",
            "external_id": "12345",
        }
    )

    handler = PipedriveOrganizationHandler(
        pipedrive=pipedrive,
        gpuaas=gpuaas,
    )

    result = await handler.handle(
        {
            "data": {
                "id": 12345,
            }
        }
    )

    assert result["id"] == "customer-123"

    pipedrive.get_organization.assert_awaited_once_with(12345)

    gpuaas.upsert_customer.assert_awaited_once_with(
        external_id="pipedrive:organization:12345",
        company_name="Acme AI",
        email="hello@acme.ai",
        country="IN",
    )

    gpuaas.link_customer_identity.assert_awaited_once_with(
        customer_id="customer-123",
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )


@pytest.mark.asyncio
async def test_organization_handler_uses_stable_identity_when_email_missing():
    pipedrive = MagicMock()
    gpuaas = MagicMock()

    pipedrive.get_organization = AsyncMock(
        return_value={
            "id": 67890,
            "name": "No Email AI",
            "country": "US",
        }
    )

    gpuaas.upsert_customer = AsyncMock(
        return_value={
            "id": "customer-456",
        }
    )

    gpuaas.link_customer_identity = AsyncMock(
        return_value={
            "id": "identity-456",
        }
    )

    handler = PipedriveOrganizationHandler(
        pipedrive=pipedrive,
        gpuaas=gpuaas,
    )

    await handler.handle(
        {
            "data": {
                "id": 67890,
            }
        }
    )

    gpuaas.link_customer_identity.assert_awaited_once_with(
        customer_id="customer-456",
        source="pipedrive",
        entity_type="organization",
        external_id="67890",
    )


@pytest.mark.asyncio
async def test_list_organizations():
    from unittest.mock import AsyncMock, MagicMock, patch

    from apps.integration_hub.app.integrations.pipedrive.client import (
        PipedriveClient,
    )

    client = PipedriveClient(
        company_domain="example",
        api_token="token",
    )

    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "success": True,
        "data": [
            {
                "id": 123,
                "name": "Acme AI",
            },
            {
                "id": 456,
                "name": "Beta Compute",
            },
        ],
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
        "apps.integration_hub.app.integrations.pipedrive.client.httpx.AsyncClient",
        return_value=context_manager,
    ):
        result = await client.list_organizations()

    assert result == [
        {
            "id": 123,
            "name": "Acme AI",
        },
        {
            "id": 456,
            "name": "Beta Compute",
        },
    ]

    http_client.get.assert_awaited_once_with(
        "https://example.pipedrive.com/api/v2/organizations",
        params={
            "api_token": "token",
        },
    )
