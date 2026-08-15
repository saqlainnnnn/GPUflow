from typing import Protocol
from uuid import UUID

from apps.ai.tools.schemas import (
    CustomerToolOutput,
    GetCustomerInput,
)
from apps.gpuaas.app.services.customer import CustomerNotFoundError


class CustomerServiceProtocol(Protocol):
    async def get_customer(
        self,
        customer_id: UUID,
    ): ...


class CustomerNotFoundToolError(Exception):
    pass


class CustomerTool:
    def __init__(
        self,
        customer_service: CustomerServiceProtocol,
    ) -> None:
        self.customer_service = customer_service

    async def get_customer(
        self,
        data: GetCustomerInput,
    ) -> CustomerToolOutput:
        try:
            customer = await self.customer_service.get_customer(
                data.customer_id,
            )
        except CustomerNotFoundError as exc:
            raise CustomerNotFoundToolError(
                f"Customer '{data.customer_id}' not found",
            ) from exc

        return CustomerToolOutput(
            id=customer.id,
            external_id=customer.external_id,
            company_name=customer.company_name,
            email=customer.email,
            country=customer.country,
            status=customer.status,
        )