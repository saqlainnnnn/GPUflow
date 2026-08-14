from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.capacity import GPUCapacity
from apps.gpuaas.app.repositories.capacity import CapacityRepository
from apps.gpuaas.app.schemas.capacity import CapacityCreate


class CapacityAlreadyExistsError(Exception):
    pass


class CapacityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = CapacityRepository(session)

    async def create_capacity(
        self,
        data: CapacityCreate,
    ) -> GPUCapacity:
        capacity = GPUCapacity(
            region=data.region,
            gpu_type=data.gpu_type,
            total_gpus=data.total_gpus,
            allocated_gpus=0,
            status="active",
        )

        self.session.add(capacity)

        try:
            await self.session.commit()
            await self.session.refresh(capacity)
        except IntegrityError as exc:
            await self.session.rollback()
            raise CapacityAlreadyExistsError(
                f"Capacity for {data.gpu_type} in {data.region} already exists"
            ) from exc

        return capacity

    async def list_capacity(self) -> list[GPUCapacity]:
        return await self.repository.list_all()
