from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from apps.integration_hub.app.api.dependencies import get_db
from apps.integration_hub.app.core.redis import get_redis
from apps.integration_hub.app.schemas.event import (
    EventCreate,
    EventIngestResponse,
    EventResponse,
)
from apps.integration_hub.app.services.event import (
    EventNotFoundError,
    EventNotReplayableError,
    EventService,
)
from apps.integration_hub.app.services.queue import EventQueue

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
    redis: Redis = Depends(get_redis),
) -> EventIngestResponse:
    service = EventService(session)

    event, created = await service.ingest(data)

    if created:
        queue = EventQueue(redis)
        await queue.enqueue(event.id)

    return EventIngestResponse(
        event=EventResponse.model_validate(event),
        created=created,
    )


@router.post(
    "/{event_id}/replay",
    response_model=EventResponse,
)
async def replay_event(
    event_id: UUID,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> EventResponse:
    service = EventService(session)

    try:
        event = await service.replay(event_id)
    except EventNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except EventNotReplayableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    queue = EventQueue(redis)

    await queue.remove_from_dlq(event.id)
    await queue.enqueue(event.id)

    return EventResponse.model_validate(event)
