from typing import Protocol
from uuid import UUID

from apps.ai.tools.schemas import (
    CreateCustomerInput,
    CustomerToolOutput,
    GetCustomerInput,
    UpdateCustomerInput,
)


class CustomerServiceProtocol(Protocol):
    async def get_customer(
        self,
        customer_id: UUID,
    ): ...

    async def create_customer(
        self,
        data,
    ): ...

    async def update_customer(
        self,
        customer_id: UUID,
        data,
    ): ...


class CustomerNotFoundToolError(Exception):
    pass


class CustomerAlreadyExistsToolError(Exception):
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
        from apps.gpuaas.app.services.customer import (
            CustomerNotFoundError,
        )

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

    async def create_customer(
        self,
        data: CreateCustomerInput,
    ) -> CustomerToolOutput:
        from apps.gpuaas.app.services.customer import (
            CustomerAlreadyExistsError,
        )

        try:
            customer = await self.customer_service.create_customer(
                data,
            )
        except CustomerAlreadyExistsError as exc:
            raise CustomerAlreadyExistsToolError(
                f"Customer with external_id "
                f"'{data.external_id}' already exists",
            ) from exc

        return CustomerToolOutput(
            id=customer.id,
            external_id=customer.external_id,
            company_name=customer.company_name,
            email=customer.email,
            country=customer.country,
            status=customer.status,
        )

    async def update_customer(
        self,
        data: UpdateCustomerInput,
    ) -> CustomerToolOutput:
        from apps.gpuaas.app.services.customer import (
            CustomerNotFoundError,
        )

        try:
            customer = await self.customer_service.update_customer(
                data.customer_id,
                data,
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
