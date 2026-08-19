from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.services.customer_reconciliation_runner import (
    CustomerReconciliationRunner,
)


def build_runner():
    reconciler = AsyncMock()
    persistence = AsyncMock()

    runner = CustomerReconciliationRunner(
        reconciler=reconciler,
        persistence=persistence,
    )

    return runner, reconciler, persistence


def build_reconciliation_result():
    result = MagicMock()

    result.source = "pipedrive"
    result.entity_type = "organization"
    result.status.value = "matched"
    result.mismatches = []
    result.missing = []
    result.fields = {
        "company_name": {
            "status": "match",
        }
    }

    return result


@pytest.mark.asyncio
async def test_reconcile_and_persist():
    runner, reconciler, persistence = build_runner()

    customer_id = uuid4()

    reconciliation = build_reconciliation_result()

    persisted = MagicMock()

    reconciler.reconcile_identity.return_value = reconciliation
    persistence.persist.return_value = persisted

    result, record = await runner.reconcile_and_persist(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        source_record={
            "company_name": "Acme AI",
            "email": "hello@acme.ai",
            "country": "IN",
        },
        adapter=MagicMock(),
    )

    assert result is reconciliation
    assert record is persisted

    reconciler.reconcile_identity.assert_awaited_once_with(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        source_record={
            "company_name": "Acme AI",
            "email": "hello@acme.ai",
            "country": "IN",
        },
        adapter=reconciler.reconcile_identity.await_args.kwargs["adapter"],
    )

    persistence.persist.assert_awaited_once_with(
        customer_id=customer_id,
        external_id="12345",
        reconciliation=reconciliation,
    )


@pytest.mark.asyncio
async def test_persistence_is_not_attempted_when_reconciliation_fails():
    runner, reconciler, persistence = build_runner()

    customer_id = uuid4()

    reconciler.reconcile_identity.side_effect = ValueError(
        "Customer identity is not linked"
    )

    with pytest.raises(
        ValueError,
        match="identity is not linked",
    ):
        await runner.reconcile_and_persist(
            customer_id=customer_id,
            source="pipedrive",
            entity_type="organization",
            external_id="12345",
            source_record={},
            adapter=MagicMock(),
        )

    persistence.persist.assert_not_awaited()
