from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.gpuaas.app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_trigger_customer_reconciliation_run(client):
    run_id = uuid4()

    run = MagicMock()
    run.id = run_id
    run.status = "completed"
    run.started_at = __import__(
        "datetime"
    ).datetime.now(__import__("datetime").timezone.utc)
    run.completed_at = __import__(
        "datetime"
    ).datetime.now(__import__("datetime").timezone.utc)
    run.processed = 10
    run.succeeded = 9
    run.failed = 1

    with patch(
        "apps.gpuaas.app.api.routes.customers."
        "CustomerReconciliationFactory"
    ) as factory_class:
        factory = factory_class.return_value

        run_service = AsyncMock()
        run_service.run.return_value = run
        factory.build_run_service.return_value = run_service

        response = await client.post(
            "/api/v1/customers/reconciliation/runs"
        )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] == str(run_id)
    assert body["status"] == "completed"
    assert body["processed"] == 10
    assert body["succeeded"] == 9
    assert body["failed"] == 1

    run_service.run.assert_awaited_once()
