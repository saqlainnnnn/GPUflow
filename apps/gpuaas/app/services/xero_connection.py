from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.xero_connection import XeroConnection
from apps.gpuaas.app.repositories.xero_connection import (
    XeroConnectionRepository,
)


class XeroConnectionNotFoundError(Exception):
    pass


class XeroConnectionService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session
        self.repository = XeroConnectionRepository(session)

    async def save_tokens(
        self,
        *,
        customer_id: UUID,
        tenant_id: str,
        tenant_name: str | None,
        access_token: str,
        refresh_token: str,
        expires_in: int,
    ) -> XeroConnection:
        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

        connection = XeroConnection(
            customer_id=customer_id,
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            xero_contact_id=None,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )

        connection = await self.repository.create_or_update(connection)

        await self.session.commit()
        await self.session.refresh(connection)

        return connection

    async def get_connection(
        self,
        customer_id: UUID,
    ) -> XeroConnection:
        connection = await self.repository.get_by_customer(customer_id)

        if connection is None:
            raise XeroConnectionNotFoundError(f"No Xero connection for customer '{customer_id}'")

        return connection

    async def set_contact_id(
        self,
        customer_id: UUID,
        contact_id: str,
    ) -> XeroConnection:
        connection = await self.get_connection(customer_id)

        connection.xero_contact_id = contact_id

        await self.session.commit()
        await self.session.refresh(connection)

        return connection
