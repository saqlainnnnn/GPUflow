from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.integration_hub.app.models.event import IntegrationEvent
from apps.integration_hub.app.repositories.event import EventRepository
from apps.integration_hub.app.schemas.event import EventCreate


class EventNotFoundError(Exception):
    pass


class EventNotReplayableError(Exception):
    pass


class EventService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = EventRepository(session)

    async def ingest(
        self,
        data: EventCreate,
    ) -> tuple[IntegrationEvent, bool]:
        existing = await self.repository.get_by_source_event(
            source=data.source,
            source_event_id=data.source_event_id,
        )

        if existing is not None:
            return existing, False

        event = IntegrationEvent(
            event_type=data.event_type,
            source=data.source,
            source_event_id=data.source_event_id,
            occurred_at=data.occurred_at,
            correlation_id=data.correlation_id,
            payload=data.payload,
        )

        try:
            event = await self.repository.create(event)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()

            existing = await self.repository.get_by_source_event(
                source=data.source,
                source_event_id=data.source_event_id,
            )

            if existing is not None:
                return existing, False

            raise

        return event, True

    async def replay(
        self,
        event_id: UUID,
    ) -> IntegrationEvent:
        event = await self.repository.get_by_id(event_id)

        if event is None:
            raise EventNotFoundError(f"Event '{event_id}' not found")

        if event.status != "dead_letter":
            raise EventNotReplayableError(f"Event '{event_id}' is not dead_letter")

        event.status = "received"
        event.retry_count = 0
        event.last_error = None

        await self.session.commit()
        await self.session.refresh(event)

        return event
