from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.allocation import GPUAllocation


class AllocationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, allocation: GPUAllocation) -> GPUAllocation:
        self.session.add(allocation)
        await self.session.flush()
        await self.session.refresh(allocation)
        return allocation

    async def get_by_id(
        self,
        allocation_id: UUID,
    ) -> GPUAllocation | None:
        result = await self.session.execute(
            select(GPUAllocation).where(GPUAllocation.id == allocation_id)
        )
        return result.scalar_one_or_none()

    async def list_by_customer(
        self,
        customer_id: UUID,
    ) -> list[GPUAllocation]:
        result = await self.session.execute(
            select(GPUAllocation)
            .where(GPUAllocation.customer_id == customer_id)
            .order_by(GPUAllocation.created_at.desc())
        )
        return list(result.scalars().all())
