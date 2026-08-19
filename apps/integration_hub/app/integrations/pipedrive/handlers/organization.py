from typing import Any

from apps.integration_hub.app.core.config import get_settings
from apps.integration_hub.app.integrations.gpuaas.client import GPUaaSClient
from apps.integration_hub.app.integrations.pipedrive.client import (
    PipedriveClient,
)


class PipedriveOrganizationHandler:
    def __init__(
        self,
        pipedrive: PipedriveClient,
        gpuaas: GPUaaSClient,
    ) -> None:
        self.pipedrive = pipedrive
        self.gpuaas = gpuaas

    async def handle(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        data = payload.get("data", {})
        organization_id = data.get("id")

        if organization_id is None:
            raise ValueError(
                "Pipedrive organization event missing data.id"
            )

        organization_id = int(organization_id)

        organization = await self.pipedrive.get_organization(
            organization_id
        )

        external_id = (
            f"pipedrive:organization:{organization['id']}"
        )

        company_name = (
            organization.get("name")
            or f"Pipedrive Organization {organization['id']}"
        )

        email = organization.get("email")

        if not email:
            email = (
                f"pipedrive-org-{organization['id']}"
                "@example.com"
            )

        country = organization.get("country") or "US"

        customer = await self.gpuaas.upsert_customer(
            external_id=external_id,
            company_name=company_name,
            email=email,
            country=country[:2].upper(),
        )

        customer_id = customer.get("id")

        if not customer_id:
            raise RuntimeError(
                "GPUaaS customer upsert response did not contain id"
            )

        await self.gpuaas.link_customer_identity(
            customer_id=customer_id,
            source="pipedrive",
            entity_type="organization",
            external_id=str(organization["id"]),
        )

        return customer


def build_pipedrive_organization_handler() -> PipedriveOrganizationHandler:
    settings = get_settings()

    return PipedriveOrganizationHandler(
        pipedrive=PipedriveClient(
            company_domain=settings.pipedrive_company_domain,
            api_token=settings.pipedrive_api_token,
        ),
        gpuaas=GPUaaSClient(
            base_url=settings.gpuaas_base_url,
        ),
    )
