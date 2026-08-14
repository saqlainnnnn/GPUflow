from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.usage_event import GPUUsageEvent
from apps.gpuaas.app.repositories.allocation import AllocationRepository
from apps.gpuaas.app.repositories.customer import CustomerRepository
from apps.gpuaas.app.repositories.usage_event import UsageEventRepository
from apps.gpuaas.app.schemas.usage_event import UsageEventCreate


class CustomerNotFoundError(Exception):
    pass


class AllocationNotFoundError(Exception):
    pass


class AllocationOwnershipError(Exception):
    pass


class GPUMismatchError(Exception):
    pass


class UsageEventAlreadyExistsError(Exception):
    def __init__(self, event: GPUUsageEvent) -> None:
        self.event = event


class UsageEventService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.events = UsageEventRepository(session)
        self.customers = CustomerRepository(session)
        self.allocations = AllocationRepository(session)

    async def create_event(
        self,
        data: UsageEventCreate,
    ) -> tuple[GPUUsageEvent, bool]:
        existing = await self.events.get_by_event_id(data.event_id)

        if existing is not None:
            return existing, False

        customer = await self.customers.get_by_id(data.customer_id)

        if customer is None:
            raise CustomerNotFoundError(
                f"Customer '{data.customer_id}' not found"
            )

        allocation = await self.allocations.get_by_id(
            data.allocation_id
        )

        if allocation is None:
            raise AllocationNotFoundError(
                f"Allocation '{data.allocation_id}' not found"
            )

        if allocation.customer_id != data.customer_id:
            raise AllocationOwnershipError(
                "Allocation does not belong to the specified customer"
            )

        if allocation.gpu_type != data.gpu_type:
            raise GPUMismatchError(
                f"GPU type mismatch: allocation={allocation.gpu_type}, "
                f"event={data.gpu_type}"
            )

        event = GPUUsageEvent(
            event_id=data.event_id,
            customer_id=data.customer_id,
            allocation_id=data.allocation_id,
            gpu_type=data.gpu_type,
            gpu_hours=data.gpu_hours,
            utilization=data.utilization,
            timestamp=data.timestamp,
        )

        self.session.add(event)

        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()

            existing = await self.events.get_by_event_id(
                data.event_id
            )

            if existing is not None:
                return existing, False

            raise

        return event, True

    async def list_customer_usage(
        self,
        customer_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[GPUUsageEvent]:
        customer = await self.customers.get_by_id(customer_id)

        if customer is None:
            raise CustomerNotFoundError(
                f"Customer '{customer_id}' not found"
            )

        return await self.events.list_by_customer(
            customer_id=customer_id,
            start=start,
            end=end,
        )
