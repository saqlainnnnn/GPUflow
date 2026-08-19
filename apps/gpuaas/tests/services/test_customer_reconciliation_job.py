from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.gpuaas.app.services.customer_reconciliation_job import (
    CustomerReconciliationJob,
)


def build_job():
    identity_repository = AsyncMock()
    registry = MagicMock()

    job = CustomerReconciliationJob(
        identity_repository=identity_repository,
        registry=registry,
    )

    return job, identity_repository, registry


def identity(
    *,
    customer_id,
    source="pipedrive",
    entity_type="organization",
    external_id="12345",
):
    item = MagicMock()

    item.customer_id = customer_id
    item.source = source
    item.entity_type = entity_type
    item.external_id = external_id

    return item


@pytest.mark.asyncio
async def test_run_dispatches_each_identity_to_registered_handler():
    job, repository, registry = build_job()

    customer_id = "customer-1"

    first_identity = identity(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    second_identity = identity(
        customer_id=customer_id,
        source="xero",
        entity_type="contact",
        external_id="contact-456",
    )

    repository.find_all.return_value = [
        first_identity,
        second_identity,
    ]

    pipedrive_handler = AsyncMock()
    xero_handler = AsyncMock()

    registry.get.side_effect = [
        pipedrive_handler,
        xero_handler,
    ]

    result = await job.run()

    assert result == {
        "processed": 2,
        "succeeded": 2,
        "failed": 0,
    }

    registry.get.assert_any_call(
        source="pipedrive",
        entity_type="organization",
    )

    registry.get.assert_any_call(
        source="xero",
        entity_type="contact",
    )

    pipedrive_handler.reconcile.assert_awaited_once_with(
        first_identity,
    )

    xero_handler.reconcile.assert_awaited_once_with(
        second_identity,
    )


@pytest.mark.asyncio
async def test_unsupported_identity_is_counted_as_failure():
    job, repository, registry = build_job()

    item = identity(
        customer_id="customer-1",
        source="hubspot",
        entity_type="company",
        external_id="999",
    )

    repository.find_all.return_value = [item]

    registry.get.return_value = None

    result = await job.run()

    assert result == {
        "processed": 1,
        "succeeded": 0,
        "failed": 1,
    }


@pytest.mark.asyncio
async def test_handler_failure_does_not_stop_remaining_identities():
    job, repository, registry = build_job()

    first = identity(
        customer_id="customer-1",
        source="pipedrive",
        entity_type="organization",
        external_id="123",
    )

    second = identity(
        customer_id="customer-2",
        source="xero",
        entity_type="contact",
        external_id="456",
    )

    repository.find_all.return_value = [
        first,
        second,
    ]

    first_handler = AsyncMock()
    second_handler = AsyncMock()

    first_handler.reconcile.side_effect = (
        RuntimeError("Pipedrive unavailable")
    )

    registry.get.side_effect = [
        first_handler,
        second_handler,
    ]

    result = await job.run()

    assert result == {
        "processed": 2,
        "succeeded": 1,
        "failed": 1,
    }

    first_handler.reconcile.assert_awaited_once_with(first)
    second_handler.reconcile.assert_awaited_once_with(second)


@pytest.mark.asyncio
async def test_job_dispatches_pipedrive_and_xero_identities():
    from uuid import uuid4

    from apps.gpuaas.app.services.customer_reconciliation_job import (
        CustomerReconciliationJob,
    )

    identity_repository = AsyncMock()
    registry = MagicMock()

    pipedrive_identity = MagicMock()
    pipedrive_identity.customer_id = uuid4()
    pipedrive_identity.source = "pipedrive"
    pipedrive_identity.entity_type = "organization"
    pipedrive_identity.external_id = "123"

    xero_identity = MagicMock()
    xero_identity.customer_id = uuid4()
    xero_identity.source = "xero"
    xero_identity.entity_type = "contact"
    xero_identity.external_id = "contact-456"

    identity_repository.find_all.return_value = [
        pipedrive_identity,
        xero_identity,
    ]

    pipedrive_handler = AsyncMock()
    xero_handler = AsyncMock()

    registry.get.side_effect = [
        pipedrive_handler,
        xero_handler,
    ]

    job = CustomerReconciliationJob(
        identity_repository=identity_repository,
        registry=registry,
    )

    result = await job.run()

    assert result == {
        "processed": 2,
        "succeeded": 2,
        "failed": 0,
    }

    pipedrive_handler.reconcile.assert_awaited_once_with(
        pipedrive_identity
    )

    xero_handler.reconcile.assert_awaited_once_with(
        xero_identity
    )
