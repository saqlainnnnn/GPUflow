from typing import Any

import httpx

from apps.gpuaas.app.core.config import get_settings


class IntegrationHubPublisher:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def publish(
        self,
        event: dict[str, Any],
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/events/ingest",
                json=event,
            )

        response.raise_for_status()

        return response.json()


def get_integration_hub_publisher() -> IntegrationHubPublisher:
    settings = get_settings()

    return IntegrationHubPublisher(
        base_url=settings.integration_hub_base_url,
    )
