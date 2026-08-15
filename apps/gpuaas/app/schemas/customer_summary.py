
from pydantic import BaseModel

from apps.gpuaas.app.schemas.allocation import AllocationResponse
from apps.gpuaas.app.schemas.customer import CustomerResponse
from apps.gpuaas.app.schemas.job import JobResponse
from apps.gpuaas.app.schemas.usage_analytics import UsageAnalyticsResponse


class CustomerSummaryResponse(BaseModel):
    customer: CustomerResponse
    allocations: list[AllocationResponse]
    jobs: list[JobResponse]
    usage: UsageAnalyticsResponse
