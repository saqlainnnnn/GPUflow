from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.api.dependencies import get_db
from apps.gpuaas.app.schemas.capacity import CapacityCreate, CapacityResponse
from apps.gpuaas.app.services.capacity import (
    CapacityAlreadyExistsError,
    CapacityService,
)

router = APIRouter(
    prefix="/capacity",
    tags=["capacity"],
)


@router.post(
    "",
    response_model=CapacityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_capacity(
    data: CapacityCreate,
    session: AsyncSession = Depends(get_db),
) -> CapacityResponse:
    service = CapacityService(session)

    try:
        capacity = await service.create_capacity(data)
    except CapacityAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return CapacityResponse.model_validate(capacity)


@router.get(
    "",
    response_model=list[CapacityResponse],
)
async def list_capacity(
    session: AsyncSession = Depends(get_db),
) -> list[CapacityResponse]:
    service = CapacityService(session)
    capacities = await service.list_capacity()

    return [CapacityResponse.model_validate(capacity) for capacity in capacities]
