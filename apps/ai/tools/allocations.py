from typing import Protocol
from uuid import UUID

from apps.ai.tools.schemas import (
    AllocationToolOutput,
    GetAllocationsInput,
)
from apps.gpuaas.app.services.allocation import (
    CustomerNotFoundError,
)


class AllocationServiceProtocol(Protocol):
    async def list_customer_allocations(
        self,
        customer_id: UUID,
    ): ...


class AllocationCustomerNotFoundError(Exception):
    pass


class AllocationTool:
    def __init__(
        self,
        allocation_service: AllocationServiceProtocol,
    ) -> None:
        self.allocation_service = allocation_service

    async def get_allocations(
        self,
        data: GetAllocationsInput,
    ) -> list[AllocationToolOutput]:
        try:
            allocations = (
                await self.allocation_service.list_customer_allocations(
                    data.customer_id,
                )
            )
        except CustomerNotFoundError as exc:
            raise AllocationCustomerNotFoundError(
                f"Customer '{data.customer_id}' not found",
            ) from exc

        return [
            AllocationToolOutput(
                id=allocation.id,
                customer_id=allocation.customer_id,
                gpu_type=allocation.gpu_type,
                gpu_count=allocation.gpu_count,
                region=allocation.region,
                status=allocation.status,
            )
            for allocation in allocations
        ]
