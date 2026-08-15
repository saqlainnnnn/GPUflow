from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class BillingLineItem(BaseModel):
    usage_event_id: UUID
    timestamp: datetime
    gpu_type: str
    gpu_hours: float = Field(ge=0)
    rate_per_gpu_hour: Decimal = Field(ge=0)
    amount: Decimal = Field(ge=0)


class CustomerBillingSummary(BaseModel):
    customer_id: UUID
    currency: str
    line_items: list[BillingLineItem]
    total_gpu_hours: float = Field(ge=0)
    subtotal: Decimal = Field(ge=0)
