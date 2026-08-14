from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.repositories.customer import CustomerRepository
from apps.gpuaas.app.repositories.usage_analytics import (
    UsageAnalyticsRepository,
)
from apps.gpuaas.app.schemas.usage_analytics import (
    DailyUsage,
    GPUTypeUsage,
    UsageAnalyticsResponse,
    UsageSummaryResponse,
)


class CustomerNotFoundError(Exception):
    pass


class UsageAnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.analytics = UsageAnalyticsRepository(session)
        self.customers = CustomerRepository(session)

    async def get_analytics(
        self,
        customer_id: UUID,
    ) -> UsageAnalyticsResponse:
        customer = await self.customers.get_by_id(customer_id)

        if customer is None:
            raise CustomerNotFoundError(f"Customer '{customer_id}' not found")

        now = datetime.now(UTC)

        total_gpu_hours, average_utilization, event_count = await self.analytics.summary(
            customer_id
        )

        gpu_hours_7d, _, _ = await self.analytics.summary(
            customer_id,
            start=now - timedelta(days=7),
        )

        previous_7d_start = now - timedelta(days=14)

        previous_7d_gpu_hours, _, _ = await self.analytics.summary(
            customer_id,
            start=previous_7d_start,
            end=now - timedelta(days=7),
        )

        gpu_hours_30d, _, _ = await self.analytics.summary(
            customer_id,
            start=now - timedelta(days=30),
        )

        previous_30d_start = now - timedelta(days=60)

        previous_30d_gpu_hours, _, _ = await self.analytics.summary(
            customer_id,
            start=previous_30d_start,
            end=now - timedelta(days=30),
        )

        growth_7d = self._growth_percent(
            gpu_hours_7d,
            previous_7d_gpu_hours,
        )

        growth_30d = self._growth_percent(
            gpu_hours_30d,
            previous_30d_gpu_hours,
        )

        summary = UsageSummaryResponse(
            customer_id=customer_id,
            total_gpu_hours=round(total_gpu_hours, 2),
            average_utilization=round(average_utilization, 4),
            event_count=event_count,
            gpu_hours_7d=round(gpu_hours_7d, 2),
            gpu_hours_30d=round(gpu_hours_30d, 2),
            growth_7d_percent=growth_7d,
            growth_30d_percent=growth_30d,
        )

        by_gpu_type = [
            GPUTypeUsage(
                gpu_type=gpu_type,
                gpu_hours=round(gpu_hours, 2),
                average_utilization=round(utilization, 4),
            )
            for gpu_type, gpu_hours, utilization in await self.analytics.by_gpu_type(customer_id)
        ]

        daily = [
            DailyUsage(
                date=timestamp.date(),
                gpu_hours=round(gpu_hours, 2),
                average_utilization=round(utilization, 4),
            )
            for timestamp, gpu_hours, utilization in await self.analytics.daily(customer_id)
        ]

        return UsageAnalyticsResponse(
            customer_id=customer_id,
            summary=summary,
            by_gpu_type=by_gpu_type,
            daily=daily,
        )

    @staticmethod
    def _growth_percent(
        current: float,
        previous: float,
    ) -> float | None:
        if previous == 0:
            if current == 0:
                return 0.0

            return None

        return round(
            ((current - previous) / previous) * 100,
            2,
        )
