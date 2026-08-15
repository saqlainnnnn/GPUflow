from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InvoiceLineItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    description: str
    gpu_type: str
    gpu_hours: Decimal
    rate_per_gpu_hour: Decimal
    amount: Decimal


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    invoice_number: str
    period_start: date
    period_end: date
    currency: str
    subtotal: Decimal
    total: Decimal
    status: str
    line_items: list[InvoiceLineItemResponse]


class InvoiceStatusUpdate(BaseModel):
    status: str
