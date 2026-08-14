from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.api.dependencies import get_db
from apps.gpuaas.app.schemas.allocation import (
    AllocationCreate,
    AllocationResponse,
)
from apps.gpuaas.app.services.allocation import (
    AllocationNotFoundError,
    AllocationService,
    CapacityNotFoundError,
    CustomerNotFoundError,
    InsufficientCapacityError,
)

router = APIRouter(
    prefix="/allocations",
    tags=["allocations"],
)


@router.post(
    "",
    response_model=AllocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_allocation(
    data: AllocationCreate,
    session: AsyncSession = Depends(get_db),
) -> AllocationResponse:
    service = AllocationService(session)

    try:
        allocation = await service.create_allocation(data)
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except CapacityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InsufficientCapacityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return AllocationResponse.model_validate(allocation)


@router.get(
    "/{allocation_id}",
    response_model=AllocationResponse,
)
async def get_allocation(
    allocation_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> AllocationResponse:
    service = AllocationService(session)

    try:
        allocation = await service.get_allocation(allocation_id)
    except AllocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return AllocationResponse.model_validate(allocation)


@router.get(
    "/customer/{customer_id}",
    response_model=list[AllocationResponse],
)
async def list_customer_allocations(
    customer_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[AllocationResponse]:
    service = AllocationService(session)

    try:
        allocations = await service.list_customer_allocations(customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return [AllocationResponse.model_validate(allocation) for allocation in allocations]
