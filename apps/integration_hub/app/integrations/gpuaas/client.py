from typing import Any

import httpx


class GPUaaSClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def create_customer(
        self,
        *,
        external_id: str,
        company_name: str,
        email: str,
        country: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/customers",
                json={
                    "external_id": external_id,
                    "company_name": company_name,
                    "email": email,
                    "country": country,
                },
            )

        response.raise_for_status()
        return response.json()

    async def get_customer_by_external_id(
        self,
        external_id: str,
    ) -> dict[str, Any] | None:
        # We'll add a proper lookup endpoint to GPUaaS shortly.
        return None

    async def reconcile_customer_source(
        self,
        *,
        customer_id: str,
        source: str,
        entity_type: str,
        external_id: str,
        source_record: dict[str, Any],
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/customers/"
                f"{customer_id}/reconciliation",
                json={
                    "source": source,
                    "entity_type": entity_type,
                    "external_id": external_id,
                    "source_record": source_record,
                },
            )

        response.raise_for_status()

        return response.json()

    async def link_customer_identity(
        self,
        *,
        customer_id: str,
        source: str,
        entity_type: str,
        external_id: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/customers/"
                f"{customer_id}/identities",
                json={
                    "source": source,
                    "entity_type": entity_type,
                    "external_id": external_id,
                },
            )

        response.raise_for_status()

        return response.json()

    async def upsert_customer(
        self,
        *,
        external_id: str,
        company_name: str,
        email: str,
        country: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.put(
                f"{self.base_url}/api/v1/customers/by-external-id/{external_id}",
                json={
                    "external_id": external_id,
                    "company_name": company_name,
                    "email": email,
                    "country": country,
                    "status": "active",
                },
            )

        response.raise_for_status()

        return response.json()
