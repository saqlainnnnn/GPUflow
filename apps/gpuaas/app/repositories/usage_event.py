from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.usage_event import GPUUsageEvent


class UsageEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_event_id(
        self,
        event_id: str,
    ) -> GPUUsageEvent | None:
        result = await self.session.execute(
            select(GPUUsageEvent).where(GPUUsageEvent.event_id == event_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        event: GPUUsageEvent,
    ) -> GPUUsageEvent:
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def list_by_customer(
        self,
        customer_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[GPUUsageEvent]:
        query = (
            select(GPUUsageEvent)
            .where(GPUUsageEvent.customer_id == customer_id)
            .order_by(GPUUsageEvent.timestamp.desc())
        )

        if start is not None:
            query = query.where(GPUUsageEvent.timestamp >= start)

        if end is not None:
            query = query.where(GPUUsageEvent.timestamp <= end)

        result = await self.session.execute(query)

        return list(result.scalars().all())
