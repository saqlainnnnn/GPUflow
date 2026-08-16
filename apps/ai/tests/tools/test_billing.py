from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from apps.ai.tools.billing import (
    BillingCustomerNotFoundError,
    BillingTool,
)
from apps.ai.tools.schemas import (
    BillingToolOutput,
    GetBillingInput,
)


@pytest.mark.asyncio
async def test_get_billing_returns_structured_output():
    customer_id = uuid4()

    billing_service = AsyncMock()

    summary = type(
        "BillingSummary",
        (),
        {
            "customer_id": customer_id,
            "currency": "USD",
            "total_gpu_hours": 1100.0,
            "subtotal": Decimal("27500.00"),
            "line_items": [
                type(
                    "LineItem",
                    (),
                    {
                        "usage_event_id": uuid4(),
                        "timestamp": None,
                        "gpu_type": "H100",
                        "gpu_hours": 500.0,
                        "rate_per_gpu_hour": Decimal("2.50"),
                        "amount": Decimal("1250.00"),
                    },
                )(),
            ],
        },
    )()

    billing_service.get_customer_billing.return_value = summary

    tool = BillingTool(billing_service)

    result = await tool.get_billing(
        GetBillingInput(
            customer_id=customer_id,
        )
    )

    assert isinstance(result, BillingToolOutput)
    assert result.customer_id == customer_id
    assert result.currency == "USD"
    assert result.total_gpu_hours == 1100.0
    assert result.subtotal == Decimal("27500.00")
    assert len(result.line_items) == 1
    assert result.line_items[0].gpu_type == "H100"

    billing_service.get_customer_billing.assert_awaited_once_with(
        customer_id,
    )


@pytest.mark.asyncio
async def test_get_billing_returns_empty_line_items():
    customer_id = uuid4()

    billing_service = AsyncMock()

    billing_service.get_customer_billing.return_value = type(
        "BillingSummary",
        (),
        {
            "customer_id": customer_id,
            "currency": "USD",
            "total_gpu_hours": 0.0,
            "subtotal": Decimal("0.00"),
            "line_items": [],
        },
    )()

    tool = BillingTool(billing_service)

    result = await tool.get_billing(
        GetBillingInput(
            customer_id=customer_id,
        )
    )

    assert result.line_items == []
    assert result.total_gpu_hours == 0.0
    assert result.subtotal == Decimal("0.00")


@pytest.mark.asyncio
async def test_get_billing_translates_missing_customer():
    from apps.gpuaas.app.services.customer import (
        CustomerNotFoundError,
    )

    customer_id = uuid4()

    billing_service = AsyncMock()
    billing_service.get_customer_billing.side_effect = (
        CustomerNotFoundError("Customer not found")
    )

    tool = BillingTool(billing_service)

    with pytest.raises(BillingCustomerNotFoundError):
        await tool.get_billing(
            GetBillingInput(
                customer_id=customer_id,
            )
        )


def test_get_billing_input_rejects_invalid_uuid():
    with pytest.raises(ValueError):
        GetBillingInput(
            customer_id="not-a-uuid",
        )
