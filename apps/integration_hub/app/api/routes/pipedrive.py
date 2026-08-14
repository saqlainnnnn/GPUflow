from typing import Any

from fastapi import APIRouter, Depends, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from apps.integration_hub.app.api.dependencies import get_db
from apps.integration_hub.app.core.redis import get_redis
from apps.integration_hub.app.integrations.pipedrive.normalizer import (
    PipedriveWebhookNormalizer,
)
from apps.integration_hub.app.schemas.event import (
    EventCreate,
    EventIngestResponse,
    EventResponse,
)
from apps.integration_hub.app.services.event import EventService
from apps.integration_hub.app.services.queue import EventQueue

router = APIRouter(
    prefix="/webhooks/pipedrive",
    tags=["pipedrive"],
)


@router.post(
    "",
    response_model=EventIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def receive_pipedrive_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> EventIngestResponse:
    payload: dict[str, Any] = await request.json()

    normalizer = PipedriveWebhookNormalizer()
    event_data: EventCreate = normalizer.normalize(payload)

    service = EventService(session)

    event, created = await service.ingest(event_data)

    if created:
        queue = EventQueue(redis)
        await queue.enqueue(event.id)

    return EventIngestResponse(
        event=EventResponse.model_validate(event),
        created=created,
    )
