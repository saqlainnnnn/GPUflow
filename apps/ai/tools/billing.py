from typing import Protocol
from uuid import UUID

from apps.ai.tools.schemas import (
    BillingLineItemToolOutput,
    BillingToolOutput,
    GetBillingInput,
)


class BillingServiceProtocol(Protocol):
    async def get_customer_billing(
        self,
        customer_id: UUID,
    ): ...


class BillingCustomerNotFoundError(Exception):
    pass


class BillingTool:
    def __init__(
        self,
        billing_service: BillingServiceProtocol,
    ) -> None:
        self.billing_service = billing_service

    async def get_billing(
        self,
        data: GetBillingInput,
    ) -> BillingToolOutput:
        from apps.gpuaas.app.services.customer import (
            CustomerNotFoundError,
        )

        try:
            summary = await self.billing_service.get_customer_billing(
                data.customer_id,
            )
        except CustomerNotFoundError as exc:
            raise BillingCustomerNotFoundError(
                f"Customer '{data.customer_id}' not found",
            ) from exc

        line_items = [
            BillingLineItemToolOutput(
                usage_event_id=item.usage_event_id,
                timestamp=(
                    item.timestamp.isoformat()
                    if item.timestamp is not None
                    else None
                ),
                gpu_type=item.gpu_type,
                gpu_hours=item.gpu_hours,
                rate_per_gpu_hour=item.rate_per_gpu_hour,
                amount=item.amount,
            )
            for item in summary.line_items
        ]

        return BillingToolOutput(
            customer_id=summary.customer_id,
            currency=summary.currency,
            line_items=line_items,
            total_gpu_hours=summary.total_gpu_hours,
            subtotal=summary.subtotal,
        )
