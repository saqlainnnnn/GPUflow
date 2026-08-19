from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.services.customer_reconciliation_source_handler import (
    CustomerReconciliationSourceHandler,
)


@pytest.mark.asyncio
async def test_source_handler_delegates_to_reconciler():
    reconciler = AsyncMock()

    handler = CustomerReconciliationSourceHandler(
        reconciler=reconciler,
    )

    customer_id = uuid4()

    identity = type(
        "Identity",
        (),
        {
            "customer_id": customer_id,
            "source": "pipedrive",
            "entity_type": "organization",
            "external_id": "12345",
        },
    )()

    reconciler.return_value = "result"

    result = await handler.reconcile(identity)

    assert result == "result"

    reconciler.assert_awaited_once_with(
        identity,
    )
