from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.xero_connection import XeroConnection


class XeroConnectionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_customer(
        self,
        customer_id: UUID,
    ) -> XeroConnection | None:
        result = await self.session.execute(
            select(XeroConnection).where(XeroConnection.customer_id == customer_id)
        )

        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        connection: XeroConnection,
    ) -> XeroConnection:
        existing = await self.get_by_customer(connection.customer_id)

        if existing is None:
            self.session.add(connection)
            await self.session.flush()
            await self.session.refresh(connection)
            return connection

        existing.tenant_id = connection.tenant_id
        existing.tenant_name = connection.tenant_name
        existing.xero_contact_id = connection.xero_contact_id
        existing.access_token = connection.access_token
        existing.refresh_token = connection.refresh_token
        existing.expires_at = connection.expires_at

        await self.session.flush()
        await self.session.refresh(existing)

        return existing
