from typing import Any

import httpx

from apps.integration_hub.app.core.config import get_settings


class PipedriveClient:
    def __init__(
        self,
        company_domain: str,
        api_token: str,
    ) -> None:
        self.base_url = f"https://{company_domain}.pipedrive.com/api/v2"
        self.api_token = api_token

    async def get_organization(
        self,
        organization_id: int,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/organizations/{organization_id}",
                params={"api_token": self.api_token},
            )

        response.raise_for_status()

        body = response.json()

        if not body.get("success"):
            raise RuntimeError(f"Pipedrive API returned unsuccessful response: {body}")

        return body["data"]

    async def get_person(
        self,
        person_id: int,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/persons/{person_id}",
                params={"api_token": self.api_token},
            )

        response.raise_for_status()

        body = response.json()

        if not body.get("success"):
            raise RuntimeError(f"Pipedrive API returned unsuccessful response: {body}")

        return body["data"]

    async def get_deal(
        self,
        deal_id: int,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/deals/{deal_id}",
                params={"api_token": self.api_token},
            )

        response.raise_for_status()

        body = response.json()

        if not body.get("success"):
            raise RuntimeError(f"Pipedrive API returned unsuccessful response: {body}")

        return body["data"]


def get_pipedrive_client() -> PipedriveClient:
    settings = get_settings()

    if not settings.pipedrive_api_token:
        raise RuntimeError("PIPEDRIVE_API_TOKEN is not configured")

    if not settings.pipedrive_company_domain:
        raise RuntimeError("PIPEDRIVE_COMPANY_DOMAIN is not configured")

    return PipedriveClient(
        company_domain=settings.pipedrive_company_domain,
        api_token=settings.pipedrive_api_token,
    )
