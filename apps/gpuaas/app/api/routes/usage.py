from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.api.dependencies import get_db
from apps.gpuaas.app.schemas.usage_event import (
    UsageEventCreate,
    UsageEventResponse,
)
from apps.gpuaas.app.services.usage_event import (
    AllocationNotFoundError,
    AllocationOwnershipError,
    CustomerNotFoundError,
    GPUMismatchError,
    UsageEventService,
)

router = APIRouter(
    prefix="/usage",
    tags=["usage"],
)


@router.post(
    "/events",
    response_model=UsageEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_usage_event(
    data: UsageEventCreate,
    session: AsyncSession = Depends(get_db),
) -> UsageEventResponse:
    service = UsageEventService(session)

    try:
        event, created = await service.create_event(data)
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except AllocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except AllocationOwnershipError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except GPUMismatchError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    response = UsageEventResponse.model_validate(event)

    if not created:
        response = response.model_copy()

    return response


@router.get(
    "/customers/{customer_id}/events",
    response_model=list[UsageEventResponse],
)
async def list_customer_usage(
    customer_id: UUID,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
) -> list[UsageEventResponse]:
    service = UsageEventService(session)

    try:
        events = await service.list_customer_usage(
            customer_id=customer_id,
            start=start,
            end=end,
        )
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return [UsageEventResponse.model_validate(event) for event in events]
