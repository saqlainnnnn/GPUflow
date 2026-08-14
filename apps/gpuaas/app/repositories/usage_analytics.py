from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.usage_event import GPUUsageEvent


class UsageAnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def summary(
        self,
        customer_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> tuple[float, float, int]:
        query = select(
            func.coalesce(func.sum(GPUUsageEvent.gpu_hours), 0.0),
            func.coalesce(func.avg(GPUUsageEvent.utilization), 0.0),
            func.count(GPUUsageEvent.id),
        ).where(GPUUsageEvent.customer_id == customer_id)

        if start is not None:
            query = query.where(GPUUsageEvent.timestamp >= start)

        if end is not None:
            query = query.where(GPUUsageEvent.timestamp <= end)

        result = await self.session.execute(query)
        gpu_hours, utilization, event_count = result.one()

        return (
            float(gpu_hours),
            float(utilization),
            int(event_count),
        )

    async def by_gpu_type(
        self,
        customer_id: UUID,
    ) -> list[tuple[str, float, float]]:
        result = await self.session.execute(
            select(
                GPUUsageEvent.gpu_type,
                func.sum(GPUUsageEvent.gpu_hours),
                func.avg(GPUUsageEvent.utilization),
            )
            .where(GPUUsageEvent.customer_id == customer_id)
            .group_by(GPUUsageEvent.gpu_type)
            .order_by(func.sum(GPUUsageEvent.gpu_hours).desc())
        )

        return [
            (gpu_type, float(gpu_hours), float(utilization))
            for gpu_type, gpu_hours, utilization in result.all()
        ]

    async def daily(
        self,
        customer_id: UUID,
    ) -> list[tuple[datetime, float, float]]:
        usage_date = func.date_trunc(
            "day",
            GPUUsageEvent.timestamp,
        )

        result = await self.session.execute(
            select(
                usage_date,
                func.sum(GPUUsageEvent.gpu_hours),
                func.avg(GPUUsageEvent.utilization),
            )
            .where(GPUUsageEvent.customer_id == customer_id)
            .group_by(usage_date)
            .order_by(usage_date.asc())
        )

        return [
            (timestamp, float(gpu_hours), float(utilization))
            for timestamp, gpu_hours, utilization in result.all()
        ]
