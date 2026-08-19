from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from apps.gpuaas.app.services.xero_customer_reconciliation_handler import (
    XeroCustomerReconciliationHandler,
)


@pytest.mark.asyncio
async def test_xero_handler_fetches_and_reconciles_contact():
    customer_id = uuid4()

    identity = MagicMock()
    identity.customer_id = customer_id
    identity.source = "xero"
    identity.entity_type = "contact"
    identity.external_id = "contact-123"

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

    runner = AsyncMock()

    runner.reconcile_and_persist.return_value = (
        "reconciliation",
        "record",
    )

    ownership_policy = MagicMock()

    handler = XeroCustomerReconciliationHandler(
        session=AsyncMock(),
        adapter=adapter,
        runner=runner,
        ownership_policy=ownership_policy,
        client_factory=MagicMock(return_value=xero),
    )

    with patch(
        "apps.gpuaas.app.services."
        "xero_customer_reconciliation_handler."
        "get_valid_connection",
        new=AsyncMock(return_value=connection),
    ):
        result = await handler.reconcile(identity)

    assert result == (
        "reconciliation",
        "record",
    )

    xero.get_contact.assert_awaited_once_with(
        "contact-123",
    )

    adapter.to_customer_record.assert_called_once_with(
        {
            "ContactID": "contact-123",
            "Name": "Acme AI",
            "EmailAddress": "hello@acme.ai",
            "Country": "IN",
        }
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
async def test_xero_handler_rejects_wrong_identity_type():
    identity = MagicMock()
    identity.source = "xero"
    identity.entity_type = "invoice"
    identity.external_id = "invoice-123"

    handler = XeroCustomerReconciliationHandler(
        session=AsyncMock(),
        adapter=MagicMock(),
        runner=AsyncMock(),
        ownership_policy=MagicMock(),
    )

    with pytest.raises(
        ValueError,
        match="unsupported Xero identity",
    ):
        await handler.reconcile(identity)
