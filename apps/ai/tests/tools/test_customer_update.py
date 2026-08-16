from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from apps.ai.tools.customer import (
    CustomerNotFoundToolError,
    CustomerTool,
)
from apps.ai.tools.schemas import (
    CustomerToolOutput,
    UpdateCustomerInput,
)


@pytest.mark.asyncio
async def test_update_customer_returns_structured_output():
    customer_id = uuid4()

    customer_service = AsyncMock()

    customer_service.update_customer.return_value = type(
        "Customer",
        (),
        {
            "id": customer_id,
            "external_id": "pd:organization:123",
            "company_name": "Acme AI Updated",
            "email": "new@acme.ai",
            "country": "US",
            "status": "active",
        },
    )()

    tool = CustomerTool(customer_service)

    result = await tool.update_customer(
        UpdateCustomerInput(
            customer_id=customer_id,
            company_name="Acme AI Updated",
            email="new@acme.ai",
            country="us",
            status="active",
            sync_origin="gpuflow",
        )
    )

    assert isinstance(result, CustomerToolOutput)
    assert result.id == customer_id
    assert result.company_name == "Acme AI Updated"
    assert result.email == "new@acme.ai"
    assert result.country == "US"

    customer_service.update_customer.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_customer_translates_missing_customer():
    from apps.gpuaas.app.services.customer import (
        CustomerNotFoundError,
    )

    customer_id = uuid4()

    customer_service = AsyncMock()

    customer_service.update_customer.side_effect = CustomerNotFoundError(
        "Customer not found",
    )

    tool = CustomerTool(customer_service)

    with pytest.raises(CustomerNotFoundToolError):
        await tool.update_customer(
            UpdateCustomerInput(
                customer_id=customer_id,
                company_name="Acme AI",
                email="ops@acme.ai",
                country="US",
                status="active",
            )
        )


def test_update_customer_validates_input():
    customer_id = uuid4()

    with pytest.raises(ValueError):
        UpdateCustomerInput(
            customer_id=customer_id,
            company_name="",
            email="ops@acme.ai",
            country="US",
            status="active",
        )

    with pytest.raises(ValueError):
        UpdateCustomerInput(
            customer_id=customer_id,
            company_name="Acme AI",
            email="not-an-email",
            country="US",
            status="active",
        )

    with pytest.raises(ValueError):
        UpdateCustomerInput(
            customer_id=customer_id,
            company_name="Acme AI",
            email="ops@acme.ai",
            country="USA",
            status="active",
        )
