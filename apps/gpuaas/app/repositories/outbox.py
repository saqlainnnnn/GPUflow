from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.outbox_event import OutboxEvent


class OutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        aggregate_type: str,
        aggregate_id: UUID,
        event_type: str,
        payload: dict,
    ) -> OutboxEvent:
        event = OutboxEvent(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=payload,
        )

        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)

        return event

    async def get_pending(
        self,
        limit: int = 50,
    ) -> list[OutboxEvent]:
        result = await self.session.execute(
            select(OutboxEvent)
            .where(
                OutboxEvent.status == "pending",
                OutboxEvent.available_at <= datetime.now(UTC),
            )
            .order_by(OutboxEvent.created_at)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def mark_processed(
        self,
        event: OutboxEvent,
    ) -> None:
        event.status = "processed"
        event.processed_at = datetime.now(UTC)
        event.last_error = None

        await self.session.flush()

    async def mark_failed(
        self,
        event: OutboxEvent,
        *,
        error: str,
    ) -> None:
        event.status = "pending"
        event.attempts += 1
        event.last_error = error

        await self.session.flush()
