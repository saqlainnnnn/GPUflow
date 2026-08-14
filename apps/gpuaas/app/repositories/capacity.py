from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.capacity import GPUCapacity


class CapacityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, capacity: GPUCapacity) -> GPUCapacity:
        self.session.add(capacity)
        await self.session.flush()
        await self.session.refresh(capacity)
        return capacity

    async def get_for_update(
        self,
        region: str,
        gpu_type: str,
    ) -> GPUCapacity | None:
        result = await self.session.execute(
            select(GPUCapacity)
            .where(
                GPUCapacity.region == region,
                GPUCapacity.gpu_type == gpu_type,
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[GPUCapacity]:
        result = await self.session.execute(
            select(GPUCapacity).order_by(
                GPUCapacity.region,
                GPUCapacity.gpu_type,
            )
        )
        return list(result.scalars().all())
