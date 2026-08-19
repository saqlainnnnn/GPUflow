from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.models.customer_reconciliation_run import (
    CustomerReconciliationRun,
)
from apps.gpuaas.app.repositories.customer_reconciliation_run import (
    CustomerReconciliationRunRepository,
)


def build_repository():
    session = AsyncMock()
    session.add = MagicMock()

    return (
        CustomerReconciliationRunRepository(session),
        session,
    )


@pytest.mark.asyncio
async def test_create_persists_run():
    repository, session = build_repository()

    run = CustomerReconciliationRun(
        status="running",
        processed=0,
        succeeded=0,
        failed=0,
    )

    result = await repository.create(run)

    assert result is run
    session.add.assert_called_once_with(run)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(run)


@pytest.mark.asyncio
async def test_get_returns_run():
    repository, session = build_repository()

    run = CustomerReconciliationRun(
        status="completed",
        processed=10,
        succeeded=9,
        failed=1,
    )

    result_proxy = MagicMock()
    result_proxy.scalar_one_or_none.return_value = run
    session.execute.return_value = result_proxy

    run_id = uuid4()

    result = await repository.get(run_id)

    assert result is run
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_returns_none_when_missing():
    repository, session = build_repository()

    result_proxy = MagicMock()
    result_proxy.scalar_one_or_none.return_value = None
    session.execute.return_value = result_proxy

    result = await repository.get(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_update_persists_run():
    repository, session = build_repository()

    run = CustomerReconciliationRun(
        status="completed",
        processed=10,
        succeeded=9,
        failed=1,
    )

    result = await repository.update(run)

    assert result is run
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(run)


@pytest.mark.asyncio
async def test_get_latest_returns_latest_run():
    repository, session = build_repository()

    run = CustomerReconciliationRun(
        status="completed",
        processed=10,
        succeeded=10,
        failed=0,
    )

    result_proxy = MagicMock()
    result_proxy.scalar_one_or_none.return_value = run
    session.execute.return_value = result_proxy

    result = await repository.get_latest()

    assert result is run
    session.execute.assert_awaited_once()
