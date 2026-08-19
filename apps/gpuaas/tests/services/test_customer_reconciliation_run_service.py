from datetime import timezone
from unittest.mock import AsyncMock

import pytest

from apps.gpuaas.app.models.customer_reconciliation_run import (
    CustomerReconciliationRun,
)
from apps.gpuaas.app.services.customer_reconciliation_run_service import (
    CustomerReconciliationRunService,
)


def build_service():
    repository = AsyncMock()
    job = AsyncMock()

    async def update(run):
        return run

    repository.update.side_effect = update

    service = CustomerReconciliationRunService(
        repository=repository,
        job=job,
    )

    return service, repository, job


@pytest.mark.asyncio
async def test_run_creates_running_record_then_completes():
    service, repository, job = build_service()

    job.run.return_value = {
        "processed": 10,
        "succeeded": 9,
        "failed": 1,
    }

    result = await service.run()

    repository.create.assert_awaited_once()
    repository.update.assert_awaited_once()

    created = repository.create.await_args.args[0]

    assert isinstance(
        created,
        CustomerReconciliationRun,
    )

    assert created.status == "completed"
    assert created.processed == 10
    assert created.succeeded == 9
    assert created.failed == 1

    assert created.started_at.tzinfo == timezone.utc
    assert created.completed_at is not None
    assert created.completed_at.tzinfo == timezone.utc

    assert result is created


@pytest.mark.asyncio
async def test_run_marks_failed_when_job_crashes():
    service, repository, job = build_service()

    job.run.side_effect = RuntimeError(
        "database unavailable"
    )

    with pytest.raises(
        RuntimeError,
        match="database unavailable",
    ):
        await service.run()

    repository.create.assert_awaited_once()
    repository.update.assert_awaited_once()

    run = repository.create.await_args.args[0]

    assert run.status == "failed"
    assert run.processed == 0
    assert run.succeeded == 0
    assert run.failed == 0
    assert run.completed_at is not None


@pytest.mark.asyncio
async def test_failed_run_preserves_partial_counts_when_job_returns_failure_counts():
    service, repository, job = build_service()

    job.run.return_value = {
        "processed": 10,
        "succeeded": 7,
        "failed": 3,
    }

    result = await service.run()

    assert result.processed == 10
    assert result.succeeded == 7
    assert result.failed == 3
    assert result.status == "completed"
