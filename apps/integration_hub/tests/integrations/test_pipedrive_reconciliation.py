from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.integration_hub.app.integrations.pipedrive.client import (
    PipedriveClient,
)
from apps.integration_hub.app.integrations.pipedrive.reconciliation import (
    PipedriveOrganizationReconciliationAdapter,
)

from apps.integration_hub.app.integrations.pipedrive.reconciliation_service import (
    PipedriveReconciliationService,
)


@pytest.mark.asyncio
async def test_pipedrive_organization_reconciliation_flow():
    pipedrive = MagicMock()
    gpuaas = MagicMock()
    adapter = PipedriveOrganizationReconciliationAdapter()

    pipedrive.get_organization = AsyncMock(
        return_value={
            "id": 12345,
            "name": "Acme AI",
            "email": "hello@acme.ai",
            "country": "IN",
            "owner_id": 10,
        }
    )

    gpuaas.reconcile_customer_source = AsyncMock(
        return_value={
            "customer_id": "customer-123",
            "source": "pipedrive",
            "entity_type": "organization",
            "status": "matched",
            "mismatches": [],
            "missing": [],
            "fields": {},
        }
    )

    service = PipedriveReconciliationService(
        pipedrive=pipedrive,
        gpuaas=gpuaas,
        adapter=adapter,
    )

    result = await service.reconcile_organization(
        customer_id="customer-123",
        organization_id=12345,
    )

    assert result["status"] == "matched"

    pipedrive.get_organization.assert_awaited_once_with(
        12345
    )

    gpuaas.reconcile_customer_source.assert_awaited_once_with(
        customer_id="customer-123",
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        source_record={
            "company_name": "Acme AI",
            "email": "hello@acme.ai",
            "country": "IN",
        },
    )
