from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from apps.ai.tools.schemas import (
    GetUsageInput,
    UsageToolOutput,
)
from apps.ai.tools.usage import (
    UsageCustomerNotFoundError,
    UsageTool,
)


@pytest.fixture
def usage_service():
    return AsyncMock()


@pytest.fixture
def usage_tool(usage_service):
    return UsageTool(usage_service)


@pytest.mark.asyncio
async def test_get_usage_returns_structured_output(
    usage_tool,
    usage_service,
):
    customer_id = uuid4()

    usage_service.get_analytics.return_value = type(
        "UsageAnalyticsResponse",
        (),
        {
            "customer_id": customer_id,
            "summary": type(
                "UsageSummary",
                (),
                {
                    "total_gpu_hours": 1250.5,
                    "average_utilization": 0.73,
                    "event_count": 48,
                    "gpu_hours_7d": 320.25,
                    "gpu_hours_30d": 1100.75,
                    "growth_7d_percent": 18.5,
                    "growth_30d_percent": 32.1,
                },
            )(),
            "by_gpu_type": [
                type(
                    "GPUTypeUsage",
                    (),
                    {
                        "gpu_type": "H100",
                        "gpu_hours": 900.0,
                        "average_utilization": 0.81,
                    },
                )(),
                type(
                    "GPUTypeUsage",
                    (),
                    {
                        "gpu_type": "A100",
                        "gpu_hours": 350.5,
                        "average_utilization": 0.62,
                    },
                )(),
            ],
            "daily": [
                type(
                    "DailyUsage",
                    (),
                    {
                        "date": date(2026, 8, 14),
                        "gpu_hours": 180.25,
                        "average_utilization": 0.76,
                    },
                )(),
            ],
        },
    )()

    result = await usage_tool.get_usage(
        GetUsageInput(
            customer_id=customer_id,
        )
    )

    assert isinstance(result, UsageToolOutput)

    assert result.customer_id == customer_id
    assert result.summary.total_gpu_hours == 1250.5
    assert result.summary.average_utilization == 0.73
    assert result.summary.event_count == 48
    assert result.summary.gpu_hours_7d == 320.25
    assert result.summary.growth_7d_percent == 18.5

    assert len(result.by_gpu_type) == 2
    assert result.by_gpu_type[0].gpu_type == "H100"
    assert result.by_gpu_type[0].gpu_hours == 900.0

    assert len(result.daily) == 1
    assert result.daily[0].date == date(2026, 8, 14)

    usage_service.get_analytics.assert_awaited_once_with(
        customer_id,
    )


@pytest.mark.asyncio
async def test_get_usage_translates_missing_customer(
    usage_tool,
    usage_service,
):
    from apps.gpuaas.app.services.usage_analytics import (
        CustomerNotFoundError,
    )

    usage_service.get_analytics.side_effect = CustomerNotFoundError(
        "Customer not found",
    )

    with pytest.raises(UsageCustomerNotFoundError):
        await usage_tool.get_usage(
            GetUsageInput(
                customer_id=uuid4(),
            )
        )


def test_get_usage_input_rejects_invalid_uuid():
    with pytest.raises(ValueError):
        GetUsageInput(
            customer_id="not-a-uuid",
        )
