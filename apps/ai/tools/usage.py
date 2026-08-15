from typing import Protocol
from uuid import UUID

from apps.ai.tools.schemas import (
    DailyUsageToolOutput,
    GetUsageInput,
    GPUTypeUsageToolOutput,
    UsageSummaryToolOutput,
    UsageToolOutput,
)
from apps.gpuaas.app.services.usage_analytics import (
    CustomerNotFoundError,
)


class UsageAnalyticsServiceProtocol(Protocol):
    async def get_analytics(
        self,
        customer_id: UUID,
    ): ...


class UsageCustomerNotFoundError(Exception):
    pass


class UsageTool:
    def __init__(
        self,
        usage_service: UsageAnalyticsServiceProtocol,
    ) -> None:
        self.usage_service = usage_service

    async def get_usage(
        self,
        data: GetUsageInput,
    ) -> UsageToolOutput:
        try:
            analytics = await self.usage_service.get_analytics(
                data.customer_id,
            )
        except CustomerNotFoundError as exc:
            raise UsageCustomerNotFoundError(
                f"Customer '{data.customer_id}' not found",
            ) from exc

        return UsageToolOutput(
            customer_id=analytics.customer_id,
            summary=UsageSummaryToolOutput(
                total_gpu_hours=analytics.summary.total_gpu_hours,
                average_utilization=analytics.summary.average_utilization,
                event_count=analytics.summary.event_count,
                gpu_hours_7d=analytics.summary.gpu_hours_7d,
                gpu_hours_30d=analytics.summary.gpu_hours_30d,
                growth_7d_percent=analytics.summary.growth_7d_percent,
                growth_30d_percent=analytics.summary.growth_30d_percent,
            ),
            by_gpu_type=[
                GPUTypeUsageToolOutput(
                    gpu_type=item.gpu_type,
                    gpu_hours=item.gpu_hours,
                    average_utilization=item.average_utilization,
                )
                for item in analytics.by_gpu_type
            ],
            daily=[
                DailyUsageToolOutput(
                    date=item.date,
                    gpu_hours=item.gpu_hours,
                    average_utilization=item.average_utilization,
                )
                for item in analytics.daily
            ],
        )
