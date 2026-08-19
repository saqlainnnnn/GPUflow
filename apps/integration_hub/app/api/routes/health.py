from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from apps.integration_hub.app.api.dependencies import get_db
from apps.integration_hub.app.core.redis import get_redis
from apps.integration_hub.app.repositories.event import EventRepository
from apps.integration_hub.app.schemas.health import (
    IntegrationHealthResponse,
)
from apps.integration_hub.app.services.integration_health import (
    IntegrationHealthService,
)
from apps.integration_hub.app.services.queue import EventQueue


router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get(
    "/integrations",
    response_model=IntegrationHealthResponse,
)
async def get_integration_health(
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> IntegrationHealthResponse:
    service = IntegrationHealthService(
        repository=EventRepository(session),
        queue=EventQueue(redis),
    )

    snapshot = await service.get_health()

    return IntegrationHealthResponse(
        event_age_seconds=snapshot.event_age_seconds,
        delivery_latency_seconds=(
            snapshot.delivery_latency_seconds
        ),
        failure_rate=snapshot.failure_rate,
        retry_depth=snapshot.retry_depth,
        dlq_depth=snapshot.dlq_depth,
    )
