from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from apps.gpuaas.app.services.customer_reconciliation_handler_registry import (
    CustomerReconciliationHandlerRegistry,
)
from apps.gpuaas.app.services.customer_reconciliation_job import (
    CustomerReconciliationJob,
)
from apps.gpuaas.app.services.pipedrive_customer_reconciliation_handler import (
    PipedriveCustomerReconciliationHandler,
)
from apps.gpuaas.app.services.xero_customer_reconciliation_handler import (
    XeroCustomerReconciliationHandler,
)


def build_identity(
    *,
    customer_id,
    source,
    entity_type,
    external_id,
):
    identity = MagicMock()
    identity.customer_id = customer_id
    identity.source = source
    identity.entity_type = entity_type
    identity.external_id = external_id
    return identity


@pytest.mark.asyncio
async def test_job_executes_real_pipedrive_handler():
    customer_id = uuid4()

    identity = build_identity(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    identities = AsyncMock()
    identities.find_all.return_value = [identity]

    runner = AsyncMock()

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

    ownership_policy = MagicMock()

    handler = PipedriveCustomerReconciliationHandler(
        pipedrive=pipedrive,
        adapter=adapter,
        runner=runner,
        ownership_policy=ownership_policy,
    )

    registry = CustomerReconciliationHandlerRegistry()

    registry.register(
        source="pipedrive",
        entity_type="organization",
        handler=handler,
    )

    job = CustomerReconciliationJob(
        identity_repository=identities,
        registry=registry,
    )

    result = await job.run()

    assert result == {
        "processed": 1,
        "succeeded": 1,
        "failed": 0,
    }

    pipedrive.get_organization.assert_awaited_once_with(
        12345,
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
async def test_job_executes_real_xero_handler():
    customer_id = uuid4()

    identity = build_identity(
        customer_id=customer_id,
        source="xero",
        entity_type="contact",
        external_id="contact-123",
    )

    identities = AsyncMock()
    identities.find_all.return_value = [identity]

    runner = AsyncMock()

    connection = MagicMock()
    connection.access_token = "access-token"
    connection.tenant_id = "tenant-123"

    xero = MagicMock()

    xero.get_contact = AsyncMock(
        return_value={
            "ContactID": "contact-123",
            "Name": "Acme AI",
            "EmailAddress": "hello@acme.ai",
            "Country": "IN",
        }
    )

    adapter = MagicMock()

    adapter.to_customer_record.return_value = {
        "company_name": "Acme AI",
        "email": "hello@acme.ai",
        "country": "IN",
    }

    ownership_policy = MagicMock()

    handler = XeroCustomerReconciliationHandler(
        session=AsyncMock(),
        adapter=adapter,
        runner=runner,
        ownership_policy=ownership_policy,
        client_factory=MagicMock(
            return_value=xero,
        ),
    )

    registry = CustomerReconciliationHandlerRegistry()

    registry.register(
        source="xero",
        entity_type="contact",
        handler=handler,
    )

    job = CustomerReconciliationJob(
        identity_repository=identities,
        registry=registry,
    )

    with patch(
        "apps.gpuaas.app.services."
        "xero_customer_reconciliation_handler."
        "get_valid_connection",
        new=AsyncMock(return_value=connection),
    ):
        result = await job.run()

    assert result == {
        "processed": 1,
        "succeeded": 1,
        "failed": 0,
    }

    xero.get_contact.assert_awaited_once_with(
        "contact-123",
    )

    runner.reconcile_and_persist.assert_awaited_once_with(
        customer_id=customer_id,
        source="xero",
        entity_type="contact",
        external_id="contact-123",
        source_record={
            "company_name": "Acme AI",
            "email": "hello@acme.ai",
            "country": "IN",
        },
        adapter=adapter,
        ownership_policy=ownership_policy,
    )


@pytest.mark.asyncio
async def test_job_continues_when_one_real_source_handler_fails():
    customer_id = uuid4()

    pipedrive_identity = build_identity(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    xero_identity = build_identity(
        customer_id=customer_id,
        source="xero",
        entity_type="contact",
        external_id="contact-123",
    )

    identities = AsyncMock()
    identities.find_all.return_value = [
        pipedrive_identity,
        xero_identity,
    ]

    pipedrive_handler = AsyncMock()
    pipedrive_handler.reconcile.side_effect = (
        RuntimeError("Pipedrive unavailable")
    )

    xero_handler = AsyncMock()
    xero_handler.reconcile.return_value = (
        "reconciliation",
        "record",
    )

    registry = CustomerReconciliationHandlerRegistry()

    registry.register(
        source="pipedrive",
        entity_type="organization",
        handler=pipedrive_handler,
    )

    registry.register(
        source="xero",
        entity_type="contact",
        handler=xero_handler,
    )

    job = CustomerReconciliationJob(
        identity_repository=identities,
        registry=registry,
    )

    result = await job.run()

    assert result == {
        "processed": 2,
        "succeeded": 1,
        "failed": 1,
    }

    xero_handler.reconcile.assert_awaited_once_with(
        xero_identity,
    )
