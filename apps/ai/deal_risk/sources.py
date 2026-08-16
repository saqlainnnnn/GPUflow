from typing import Any
from uuid import UUID

from apps.gpuaas.app.services.billing import BillingService
from apps.gpuaas.app.services.job import JobService


class GPUaaSJobSource:
    def __init__(
        self,
        *,
        session: Any,
        job_service: JobService | None,
    ) -> None:
        if job_service is None:
            raise ValueError("job_service is required")

        self.session = session
        self.job_service = job_service

    async def get_jobs(
        self,
        *,
        customer_id: UUID,
    ) -> list[Any]:
        return await self.job_service.list_customer_jobs(
            customer_id,
        )


class GPUaaSBillingSource:
    def __init__(
        self,
        *,
        session: Any,
        billing_service: BillingService | None,
    ) -> None:
        if billing_service is None:
            raise ValueError("billing_service is required")

        self.session = session
        self.billing_service = billing_service

    async def get_billing(
        self,
        *,
        customer_id: UUID,
    ) -> Any:
        return await self.billing_service.get_customer_billing(
            customer_id,
        )
