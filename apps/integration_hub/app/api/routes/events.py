from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.integration_hub.app.db.session import get_db
from apps.integration_hub.app.schemas.event import (
    EventCreate,
    EventIngestResponse,
    EventResponse,
)
from apps.integration_hub.app.services.event import EventService

router = APIRouter(
    prefix="/events",
    tags=["events"],
)


@router.post(
    "/ingest",
    response_model=EventIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_event(
    data: EventCreate,
    session: AsyncSession = Depends(get_db),
) -> EventIngestResponse:
    service = EventService(session)

    event, created = await service.ingest(data)

    return EventIngestResponse(
        event=EventResponse.model_validate(event),
        created=created,
    )
