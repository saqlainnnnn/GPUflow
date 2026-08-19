from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.services.pipedrive_customer_reconciliation_handler import (
    PipedriveCustomerReconciliationHandler,
)


@pytest.mark.asyncio
async def test_pipedrive_handler_fetches_and_reconciles_organization():
    customer_id = uuid4()

    identity = MagicMock()
    identity.customer_id = customer_id
    identity.source = "pipedrive"
    identity.entity_type = "organization"
    identity.external_id = "12345"

    pipedrive = AsyncMock()

    pipedrive.get_organization.return_value = {
        "id": 12345,
        "name": "Acme AI",
        "email": "hello@acme.ai",
        "country": "IN",
    }

    adapter = MagicMock()

    adapter.to_customer_record.return_value = {
        "company_name": "Acme AI",
        "email": "hello@acme.ai",
        "country": "IN",
    }

    runner = AsyncMock()
    runner.reconcile_and_persist.return_value = (
        "reconciliation",
        "record",
    )

    ownership_policy = MagicMock()

    handler = PipedriveCustomerReconciliationHandler(
        pipedrive=pipedrive,
        adapter=adapter,
        runner=runner,
        ownership_policy=ownership_policy,
    )

    result = await handler.reconcile(identity)

    assert result == (
        "reconciliation",
        "record",
    )

    pipedrive.get_organization.assert_awaited_once_with(
        12345,
    )

    adapter.to_customer_record.assert_called_once_with(
        {
            "id": 12345,
            "name": "Acme AI",
            "email": "hello@acme.ai",
            "country": "IN",
        }
    )

    runner.reconcile_and_persist.assert_awaited_once_with(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        source_record={
            "company_name": "Acme AI",
            "email": "hello@acme.ai",
            "country": "IN",
        },
        adapter=adapter,
        ownership_policy=ownership_policy,
    )


@pytest.mark.asyncio
async def test_pipedrive_handler_rejects_wrong_identity_type():
    identity = MagicMock()
    identity.source = "pipedrive"
    identity.entity_type = "person"
    identity.external_id = "12345"

    handler = PipedriveCustomerReconciliationHandler(
        pipedrive=AsyncMock(),
        adapter=MagicMock(),
        runner=AsyncMock(),
        ownership_policy=MagicMock(),
    )

    with pytest.raises(
        ValueError,
        match="unsupported Pipedrive identity",
    ):
        await handler.reconcile(identity)
