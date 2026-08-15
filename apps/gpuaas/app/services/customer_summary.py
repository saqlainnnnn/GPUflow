from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.repositories.allocation import AllocationRepository
from apps.gpuaas.app.repositories.customer import CustomerRepository
from apps.gpuaas.app.repositories.job import JobRepository
from apps.gpuaas.app.schemas.allocation import AllocationResponse
from apps.gpuaas.app.schemas.customer import CustomerResponse
from apps.gpuaas.app.schemas.customer_summary import (
    CustomerSummaryResponse,
)
from apps.gpuaas.app.schemas.job import JobResponse
from apps.gpuaas.app.services.usage_analytics import (
    UsageAnalyticsService,
)


class CustomerSummaryService:
    def __init__(self, session: AsyncSession) -> None:
        self.customers = CustomerRepository(session)
        self.allocations = AllocationRepository(session)
        self.jobs = JobRepository(session)
        self.analytics = UsageAnalyticsService(session)

    async def get_summary(
        self,
        customer_id: UUID,
    ) -> CustomerSummaryResponse:
        customer = await self.customers.get_by_id(customer_id)

        if customer is None:
            raise ValueError(f"Customer '{customer_id}' not found")

        allocations = await self.allocations.list_by_customer(customer_id)

        jobs = await self.jobs.list_by_customer(customer_id)

        usage = await self.analytics.get_analytics(customer_id)

        return CustomerSummaryResponse(
            customer=CustomerResponse.model_validate(customer),
            allocations=[
                AllocationResponse.model_validate(allocation) for allocation in allocations
            ],
            jobs=[JobResponse.model_validate(job) for job in jobs],
            usage=usage,
        )
