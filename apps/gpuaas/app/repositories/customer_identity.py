from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.customer_identity import (
    CustomerIdentity,
)


class CustomerIdentityRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def find_by_external_identity(
        self,
        *,
        source: str,
        entity_type: str,
        external_id: str,
    ) -> CustomerIdentity | None:
        result = await self.session.execute(
            select(CustomerIdentity).where(
                CustomerIdentity.source == source,
                CustomerIdentity.entity_type == entity_type,
                CustomerIdentity.external_id == external_id,
            )
        )

        return result.scalar_one_or_none()

    async def find_for_customer(
        self,
        customer_id: UUID,
    ) -> list[CustomerIdentity]:
        result = await self.session.execute(
            select(CustomerIdentity)
            .where(
                CustomerIdentity.customer_id == customer_id
            )
            .order_by(
                CustomerIdentity.created_at.asc()
            )
        )

        return list(result.scalars().all())

    async def find_all(
        self,
    ) -> list[CustomerIdentity]:
        result = await self.session.execute(
            select(CustomerIdentity)
            .order_by(
                CustomerIdentity.created_at.asc()
            )
        )

        return list(result.scalars().all())

    async def create(
        self,
        identity: CustomerIdentity,
    ) -> CustomerIdentity:
        self.session.add(identity)

        await self.session.flush()
        await self.session.refresh(identity)

        return identity
