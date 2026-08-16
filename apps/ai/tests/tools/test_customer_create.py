from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from apps.ai.tools.customer import (
    CustomerAlreadyExistsToolError,
    CustomerTool,
)
from apps.ai.tools.schemas import (
    CreateCustomerInput,
    CustomerToolOutput,
)


@pytest.mark.asyncio
async def test_create_customer_returns_structured_output():
    customer_id = uuid4()

    customer_service = AsyncMock()

    customer_service.create_customer.return_value = type(
        "Customer",
        (),
        {
            "id": customer_id,
            "external_id": "pd:organization:123",
            "company_name": "Acme AI",
            "email": "ops@acme.ai",
            "country": "US",
            "status": "active",
        },
    )()

    tool = CustomerTool(customer_service)

    result = await tool.create_customer(
        CreateCustomerInput(
            external_id="pd:organization:123",
            company_name="Acme AI",
            email="ops@acme.ai",
            country="us",
            status="active",
        )
    )

    assert isinstance(result, CustomerToolOutput)
    assert result.id == customer_id
    assert result.external_id == "pd:organization:123"
    assert result.company_name == "Acme AI"
    assert result.country == "US"

    customer_service.create_customer.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_customer_translates_duplicate_error():
    from apps.gpuaas.app.services.customer import (
        CustomerAlreadyExistsError,
    )

    customer_service = AsyncMock()

    customer_service.create_customer.side_effect = (
        CustomerAlreadyExistsError(
            "Customer already exists",
        )
    )

    tool = CustomerTool(customer_service)

    with pytest.raises(CustomerAlreadyExistsToolError):
        await tool.create_customer(
            CreateCustomerInput(
                external_id="pd:organization:123",
                company_name="Acme AI",
                email="ops@acme.ai",
                country="US",
            )
        )


def test_create_customer_validates_required_fields():
    with pytest.raises(ValueError):
        CreateCustomerInput(
            external_id="",
            company_name="Acme AI",
            email="ops@acme.ai",
            country="US",
        )

    with pytest.raises(ValueError):
        CreateCustomerInput(
            external_id="pd:organization:123",
            company_name="Acme AI",
            email="not-an-email",
            country="US",
        )
