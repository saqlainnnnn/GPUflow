from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.integrations.xero.client import XeroClient
from apps.gpuaas.app.integrations.xero.token_manager import (
    get_valid_connection,
)


class XeroAPIService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create_invoice(
        self,
        customer_id: UUID,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        connection = await get_valid_connection(
            self.session,
            customer_id,
        )

        client = XeroClient(
            access_token=connection.access_token,
            tenant_id=connection.tenant_id,
        )

        return await client.create_invoice(payload)

    async def get_invoice(
        self,
        customer_id: UUID,
        invoice_id: str,
    ) -> dict[str, Any]:
        connection = await get_valid_connection(
            self.session,
            customer_id,
        )

        client = XeroClient(
            access_token=connection.access_token,
            tenant_id=connection.tenant_id,
        )

        return await client.get_invoice(invoice_id)
