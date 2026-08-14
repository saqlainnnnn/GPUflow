from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.allocation import GPUAllocation
from apps.gpuaas.app.repositories.allocation import AllocationRepository
from apps.gpuaas.app.repositories.capacity import CapacityRepository
from apps.gpuaas.app.repositories.customer import CustomerRepository
from apps.gpuaas.app.schemas.allocation import AllocationCreate


class CustomerNotFoundError(Exception):
    pass


class CapacityNotFoundError(Exception):
    pass


class InsufficientCapacityError(Exception):
    pass


class AllocationNotFoundError(Exception):
    pass


class AllocationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.customers = CustomerRepository(session)
        self.allocations = AllocationRepository(session)
        self.capacity = CapacityRepository(session)

    async def create_allocation(
        self,
        data: AllocationCreate,
    ) -> GPUAllocation:
        customer = await self.customers.get_by_id(data.customer_id)

        if customer is None:
            raise CustomerNotFoundError(f"Customer '{data.customer_id}' not found")

        capacity = await self.capacity.get_for_update(
            region=data.region,
            gpu_type=data.gpu_type,
        )

        if capacity is None:
            raise CapacityNotFoundError(
                f"No capacity pool exists for {data.gpu_type} in {data.region}"
            )

        available = capacity.total_gpus - capacity.allocated_gpus

        if available < data.gpu_count:
            raise InsufficientCapacityError(
                f"Insufficient {data.gpu_type} capacity in "
                f"{data.region}: requested={data.gpu_count}, "
                f"available={available}"
            )

        allocation = GPUAllocation(
            customer_id=data.customer_id,
            gpu_type=data.gpu_type,
            gpu_count=data.gpu_count,
            region=data.region,
            status="active",
        )

        capacity.allocated_gpus += data.gpu_count

        await self.allocations.create(allocation)
        await self.session.commit()

        return allocation

    async def get_allocation(
        self,
        allocation_id: UUID,
    ) -> GPUAllocation:
        allocation = await self.allocations.get_by_id(allocation_id)

        if allocation is None:
            raise AllocationNotFoundError(f"Allocation '{allocation_id}' not found")

        return allocation

    async def list_customer_allocations(
        self,
        customer_id: UUID,
    ) -> list[GPUAllocation]:
        customer = await self.customers.get_by_id(customer_id)

        if customer is None:
            raise CustomerNotFoundError(f"Customer '{customer_id}' not found")

        return await self.allocations.list_by_customer(customer_id)
