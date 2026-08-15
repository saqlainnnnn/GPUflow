from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.api.dependencies import get_db
from apps.gpuaas.app.schemas.invoice import (
    InvoiceResponse,
    InvoiceStatusUpdate,
)
from apps.gpuaas.app.services.invoice import (
    CustomerNotFoundError,
    InvalidInvoiceStatusError,
    InvoiceNotFoundError,
    InvoiceService,
)

router = APIRouter(
    prefix="/invoices",
    tags=["invoices"],
)


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invoice(
    customer_id: UUID,
    period_start: date = Query(...),
    period_end: date = Query(...),
    session: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    service = InvoiceService(session)

    try:
        invoice = await service.create_invoice(
            customer_id,
            period_start,
            period_end,
        )
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return InvoiceResponse.model_validate(invoice)


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
)
async def get_invoice(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    service = InvoiceService(session)

    try:
        invoice = await service.get_invoice(invoice_id)
    except InvoiceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return InvoiceResponse.model_validate(invoice)


@router.get(
    "/customer/{customer_id}",
    response_model=list[InvoiceResponse],
)
async def list_customer_invoices(
    customer_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[InvoiceResponse]:
    service = InvoiceService(session)

    try:
        invoices = await service.list_customer_invoices(customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return [InvoiceResponse.model_validate(invoice) for invoice in invoices]


@router.post(
    "/{invoice_id}/status",
    response_model=InvoiceResponse,
)
async def update_invoice_status(
    invoice_id: UUID,
    data: InvoiceStatusUpdate,
    session: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    service = InvoiceService(session)

    try:
        invoice = await service.update_status(
            invoice_id,
            data.status,
        )
    except InvoiceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidInvoiceStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return InvoiceResponse.model_validate(invoice)
