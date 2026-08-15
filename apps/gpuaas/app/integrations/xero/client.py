from typing import Any

import httpx

XERO_API_BASE = "https://api.xero.com/api.xro/2.0"


class XeroClient:
    def __init__(
        self,
        access_token: str,
        tenant_id: str,
    ) -> None:
        self.access_token = access_token
        self.tenant_id = tenant_id

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": (f"Bearer {self.access_token}"),
            "xero-tenant-id": self.tenant_id,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def create_contact(
        self,
        *,
        name: str,
        email: str | None = None,
    ) -> dict[str, Any]:
        contact: dict[str, Any] = {
            "Name": name,
        }

        if email:
            contact["EmailAddress"] = email

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{XERO_API_BASE}/Contacts",
                headers=self._headers(),
                json={
                    "Contacts": [contact],
                },
            )

        response.raise_for_status()

        return response.json()

    async def find_contact_by_email(
        self,
        email: str,
    ) -> dict[str, Any] | None:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{XERO_API_BASE}/Contacts",
                headers=self._headers(),
                params={
                    "where": f'EmailAddress="{email}"',
                },
            )

        response.raise_for_status()

        contacts = response.json().get(
            "Contacts",
            [],
        )

        if not contacts:
            return None

        return contacts[0]

    async def find_contact_by_name(
        self,
        name: str,
    ) -> dict[str, Any] | None:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{XERO_API_BASE}/Contacts",
                headers=self._headers(),
                params={
                    "where": f'Name="{name}"',
                },
            )

        response.raise_for_status()

        contacts = response.json().get(
            "Contacts",
            [],
        )

        if not contacts:
            return None

        return contacts[0]

    async def create_invoice(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{XERO_API_BASE}/Invoices",
                headers=self._headers(),
                json={
                    "Invoices": [payload],
                },
            )

        response.raise_for_status()

        return response.json()

    async def get_invoice(
        self,
        invoice_id: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{XERO_API_BASE}/Invoices/{invoice_id}",
                headers=self._headers(),
            )

        response.raise_for_status()

        return response.json()
