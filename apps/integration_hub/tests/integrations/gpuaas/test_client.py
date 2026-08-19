from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.integration_hub.app.integrations.gpuaas.client import (
    GPUaaSClient,
)


@pytest.mark.asyncio
async def test_link_customer_identity_posts_to_identity_endpoint():
    client = GPUaaSClient(
        base_url="http://localhost:8001",
    )

    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "id": "identity-123",
        "customer_id": "customer-123",
        "source": "pipedrive",
        "entity_type": "organization",
        "external_id": "456",
    }

    http_client = AsyncMock()
    http_client.post.return_value = response

    context_manager = MagicMock()
    context_manager.__aenter__ = AsyncMock(
        return_value=http_client,
    )
    context_manager.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "apps.integration_hub.app.integrations.gpuaas.client.httpx.AsyncClient",
        return_value=context_manager,
    ):
        result = await client.link_customer_identity(
            customer_id="customer-123",
            source="pipedrive",
            entity_type="organization",
            external_id="456",
        )

    assert result == response.json()

    http_client.post.assert_awaited_once_with(
        "http://localhost:8001/api/v1/customers/customer-123/identities",
        json={
            "source": "pipedrive",
            "entity_type": "organization",
            "external_id": "456",
        },
    )

    response.raise_for_status.assert_called_once()


@pytest.mark.asyncio
async def test_link_customer_identity_propagates_http_errors():
    client = GPUaaSClient(
        base_url="http://localhost:8001",
    )

    response = MagicMock()
    response.raise_for_status.side_effect = RuntimeError("conflict")

    http_client = AsyncMock()
    http_client.post.return_value = response

    context_manager = MagicMock()
    context_manager.__aenter__ = AsyncMock(
        return_value=http_client,
    )
    context_manager.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "apps.integration_hub.app.integrations.gpuaas.client.httpx.AsyncClient",
        return_value=context_manager,
    ):
        with pytest.raises(RuntimeError, match="conflict"):
            await client.link_customer_identity(
                customer_id="customer-123",
                source="pipedrive",
                entity_type="organization",
                external_id="456",
            )
