from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.integration_hub.app.integrations.gpuaas.client import (
    GPUaaSClient,
)


@pytest.mark.asyncio
async def test_reconcile_customer_source_posts_reconciliation_request():
    client = GPUaaSClient(
        base_url="http://localhost:8001",
    )

    response = MagicMock()

    response.raise_for_status = MagicMock()

    response.json.return_value = {
        "customer_id": "customer-123",
        "source": "pipedrive",
        "entity_type": "organization",
        "status": "matched",
        "mismatches": [],
        "missing": [],
        "fields": {},
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
        result = await client.reconcile_customer_source(
            customer_id="customer-123",
            source="pipedrive",
            entity_type="organization",
            external_id="12345",
            source_record={
                "company_name": "Acme AI",
                "email": "hello@acme.ai",
                "country": "IN",
            },
        )

    assert result == response.json()

    http_client.post.assert_awaited_once_with(
        "http://localhost:8001/api/v1/customers/"
        "customer-123/reconciliation",
        json={
            "source": "pipedrive",
            "entity_type": "organization",
            "external_id": "12345",
            "source_record": {
                "company_name": "Acme AI",
                "email": "hello@acme.ai",
                "country": "IN",
            },
        },
    )

    response.raise_for_status.assert_called_once()
