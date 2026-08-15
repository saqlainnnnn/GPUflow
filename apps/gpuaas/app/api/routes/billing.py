from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.api.dependencies import get_db
from apps.gpuaas.app.schemas.billing import (
    CustomerBillingSummary,
)
from apps.gpuaas.app.services.billing import BillingService

router = APIRouter(
    prefix="/billing",
    tags=["billing"],
)


@router.get(
    "/customers/{customer_id}",
    response_model=CustomerBillingSummary,
)
async def get_customer_billing(
    customer_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> CustomerBillingSummary:
    service = BillingService(session)

    return await service.get_customer_billing(customer_id)
