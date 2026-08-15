from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.core.pricing import get_gpu_hourly_rate
from apps.gpuaas.app.repositories.usage_event import UsageEventRepository
from apps.gpuaas.app.schemas.billing import (
    BillingLineItem,
    CustomerBillingSummary,
)


class BillingService:
    def __init__(self, session: AsyncSession) -> None:
        self.events = UsageEventRepository(session)

    async def get_customer_billing(
        self,
        customer_id: UUID,
    ) -> CustomerBillingSummary:
        events = await self.events.list_by_customer(
            customer_id=customer_id,
        )

        line_items: list[BillingLineItem] = []

        total_gpu_hours = Decimal("0")
        subtotal = Decimal("0")

        for event in events:
            rate = get_gpu_hourly_rate(event.gpu_type)

            gpu_hours = Decimal(str(event.gpu_hours))

            amount = (gpu_hours * rate).quantize(Decimal("0.01"))

            line_items.append(
                BillingLineItem(
                    usage_event_id=event.id,
                    timestamp=event.timestamp,
                    gpu_type=event.gpu_type,
                    gpu_hours=float(gpu_hours),
                    rate_per_gpu_hour=rate,
                    amount=amount,
                )
            )

            total_gpu_hours += gpu_hours
            subtotal += amount

        return CustomerBillingSummary(
            customer_id=customer_id,
            currency="USD",
            line_items=line_items,
            total_gpu_hours=float(total_gpu_hours),
            subtotal=subtotal.quantize(Decimal("0.01")),
        )
