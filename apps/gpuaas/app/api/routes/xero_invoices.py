from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.api.dependencies import get_db
from apps.gpuaas.app.integrations.xero.client import XeroAPIError
from apps.gpuaas.app.services.xero_invoice import (
    XeroInvoiceCurrencyError,
    XeroInvoiceService,
)

router = APIRouter(
    prefix="/xero/invoices",
    tags=["xero"],
)


@router.post(
    "/{invoice_id}",
    status_code=status.HTTP_201_CREATED,
)
async def create_xero_invoice(
    invoice_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> dict:
    service = XeroInvoiceService(session)

    try:
        return await service.create_xero_invoice(invoice_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except XeroInvoiceCurrencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except XeroAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.response_body,
        ) from exc
