from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from apps.integration_hub.app.main import app
from apps.integration_hub.app.services.integration_health import (
    IntegrationHealthSnapshot,
)


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_get_integration_health(client):
    snapshot = IntegrationHealthSnapshot(
        event_age_seconds=120,
        delivery_latency_seconds=10.0,
        failure_rate=0.5,
        retry_depth=1.0,
        dlq_depth=3,
    )

    with patch(
        "apps.integration_hub.app.api.routes.health."
        "IntegrationHealthService"
    ) as service_class:
        service = service_class.return_value
        service.get_health = AsyncMock(
            return_value=snapshot
        )

        response = await client.get(
            "/api/v1/health/integrations"
        )

    assert response.status_code == 200

    assert response.json() == {
        "event_age_seconds": 120,
        "delivery_latency_seconds": 10.0,
        "failure_rate": 0.5,
        "retry_depth": 1.0,
        "dlq_depth": 3,
    }

    service.get_health.assert_awaited_once()
