from apps.integration_hub.app.integrations.gpuaas.client import (
    GPUaaSClient,
)
from apps.integration_hub.app.integrations.pipedrive.client import (
    PipedriveClient,
)
from apps.integration_hub.app.integrations.pipedrive.reconciliation import (
    PipedriveOrganizationReconciliationAdapter,
)


class PipedriveReconciliationService:
    def __init__(
        self,
        *,
        pipedrive: PipedriveClient,
        gpuaas: GPUaaSClient,
        adapter: PipedriveOrganizationReconciliationAdapter | None = None,
    ) -> None:
        self.pipedrive = pipedrive
        self.gpuaas = gpuaas
        self.adapter = (
            adapter
            or PipedriveOrganizationReconciliationAdapter()
        )

    async def reconcile_organization(
        self,
        *,
        customer_id: str,
        organization_id: int,
    ) -> dict:
        organization = await self.pipedrive.get_organization(
            organization_id
        )

        source_record = self.adapter.to_customer_record(
            organization
        )

        return await self.gpuaas.reconcile_customer_source(
            customer_id=customer_id,
            source="pipedrive",
            entity_type="organization",
            external_id=str(organization_id),
            source_record=source_record,
        )
