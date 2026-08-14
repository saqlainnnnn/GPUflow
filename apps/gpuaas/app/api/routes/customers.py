from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.api.dependencies import get_db
from apps.gpuaas.app.schemas.customer import CustomerCreate, CustomerResponse
from apps.gpuaas.app.services.customer import (
    CustomerAlreadyExistsError,
    CustomerNotFoundError,
    CustomerService,
)

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer(
    data: CustomerCreate,
    session: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    service = CustomerService(session)

    try:
        customer = await service.create_customer(data)
    except CustomerAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return CustomerResponse.model_validate(customer)


@router.get(
    "",
    response_model=list[CustomerResponse],
)
async def list_customers(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
) -> list[CustomerResponse]:
    service = CustomerService(session)

    customers = await service.list_customers(
        offset=offset,
        limit=limit,
    )

    return [CustomerResponse.model_validate(customer) for customer in customers]


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
async def get_customer(
    customer_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    service = CustomerService(session)

    try:
        customer = await service.get_customer(customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return CustomerResponse.model_validate(customer)
