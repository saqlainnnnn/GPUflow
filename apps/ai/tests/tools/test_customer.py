from uuid import uuid4

import pytest

from apps.ai.tools.customer import (
    CustomerNotFoundToolError,
    CustomerTool,
)
from apps.ai.tools.schemas import (
    CustomerToolOutput,
    GetCustomerInput,
)
from apps.gpuaas.app.services.customer import CustomerNotFoundError


class FakeCustomerService:
    def __init__(self) -> None:
        self.customer_id = None
        self.raise_not_found = False

    async def get_customer(self, customer_id):
        if self.raise_not_found:
            raise CustomerNotFoundError(
                f"Customer '{customer_id}' not found"
            )

        if self.customer_id is None:
            raise RuntimeError("customer not configured")

        if customer_id != self.customer_id:
            raise CustomerNotFoundError(
                f"Customer '{customer_id}' not found"
            )

        return type(
            "Customer",
            (),
            {
                "id": customer_id,
                "external_id": "pd-org-123",
                "company_name": "Acme AI",
                "email": "ops@acme.ai",
                "country": "IN",
                "status": "active",
            },
        )()


@pytest.fixture
def customer_service():
    return FakeCustomerService()


@pytest.mark.asyncio
async def test_get_customer_returns_structured_customer(
    customer_service,
):
    customer_id = uuid4()
    customer_service.customer_id = customer_id

    tool = CustomerTool(customer_service)

    result = await tool.get_customer(
        GetCustomerInput(
            customer_id=customer_id,
        )
    )

    assert isinstance(result, CustomerToolOutput)
    assert result.id == customer_id
    assert result.external_id == "pd-org-123"
    assert result.company_name == "Acme AI"
    assert result.email == "ops@acme.ai"
    assert result.country == "IN"
    assert result.status == "active"


@pytest.mark.asyncio
async def test_get_customer_returns_json_serializable_output(
    customer_service,
):
    customer_id = uuid4()
    customer_service.customer_id = customer_id

    tool = CustomerTool(customer_service)

    result = await tool.get_customer(
        GetCustomerInput(
            customer_id=customer_id,
        )
    )

    payload = result.model_dump(mode="json")

    assert payload == {
        "id": str(customer_id),
        "external_id": "pd-org-123",
        "company_name": "Acme AI",
        "email": "ops@acme.ai",
        "country": "IN",
        "status": "active",
    }


@pytest.mark.asyncio
async def test_get_customer_translates_missing_customer_error(
    customer_service,
):
    customer_service.raise_not_found = True

    tool = CustomerTool(customer_service)

    with pytest.raises(CustomerNotFoundToolError):
        await tool.get_customer(
            GetCustomerInput(
                customer_id=uuid4(),
            )
        )


def test_get_customer_input_rejects_invalid_uuid():
    with pytest.raises(ValueError):
        GetCustomerInput(
            customer_id="not-a-uuid",
        )
