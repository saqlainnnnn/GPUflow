from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.integration_hub.app.models.event import IntegrationEvent
from apps.integration_hub.app.repositories.event import EventRepository
from apps.integration_hub.app.schemas.event import EventCreate


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
