from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.api.dependencies import get_db
from apps.gpuaas.app.schemas.usage_analytics import (
    UsageAnalyticsResponse,
)
from apps.gpuaas.app.services.usage_analytics import (
    CustomerNotFoundError,
    UsageAnalyticsService,
)

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)


@router.get(
    "/customers/{customer_id}/usage",
    response_model=UsageAnalyticsResponse,
)
async def get_customer_usage_analytics(
    customer_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> UsageAnalyticsResponse:
    service = UsageAnalyticsService(session)

    try:
        return await service.get_analytics(customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
