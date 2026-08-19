from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.models.customer_reconciliation_run import (
    CustomerReconciliationRun,
)
from apps.gpuaas.app.services.customer_reconciliation_run_service import (
    CustomerReconciliationRunService,
)


@pytest.mark.asyncio
async def test_full_reconciliation_run_lifecycle():
    run_repository = AsyncMock()
    job = AsyncMock()

    job.run.return_value = {
        "processed": 3,
        "succeeded": 2,
        "failed": 1,
    }

    async def update(run):
        return run

    run_repository.update.side_effect = update

    service = CustomerReconciliationRunService(
        repository=run_repository,
        job=job,
    )

    result = await service.run()

    run_repository.create.assert_awaited_once()
    run_repository.update.assert_awaited_once()

    created_run = (
        run_repository.create.await_args.args[0]
    )

    assert isinstance(
        created_run,
        CustomerReconciliationRun,
    )

    assert result is created_run

    assert result.status == "completed"
    assert result.processed == 3
    assert result.succeeded == 2
    assert result.failed == 1

    assert result.started_at is not None
    assert result.completed_at is not None

    job.run.assert_awaited_once()
