from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from apps.ai.tools.allocations import (
    AllocationCustomerNotFoundError,
    AllocationTool,
)
from apps.ai.tools.schemas import (
    AllocationToolOutput,
    GetAllocationsInput,
)


@pytest.fixture
def allocation_service():
    return type("AllocationService", (), {})()


@pytest.fixture
def allocation_tool(allocation_service):
    return AllocationTool(allocation_service)


@pytest.mark.asyncio
async def test_get_allocations_returns_structured_output(
    allocation_tool,
    allocation_service,
):
    customer_id = uuid4()

    allocation_service.list_customer_allocations = AsyncMock(
        return_value=[
            type(
                "Allocation",
                (),
                {
                    "id": uuid4(),
                    "customer_id": customer_id,
                    "gpu_type": "H100",
                    "gpu_count": 8,
                    "region": "us-east",
                    "status": "active",
                },
            )(),
            type(
                "Allocation",
                (),
                {
                    "id": uuid4(),
                    "customer_id": customer_id,
                    "gpu_type": "A100",
                    "gpu_count": 16,
                    "region": "eu-west",
                    "status": "active",
                },
            )(),
        ],
    )

    result = await allocation_tool.get_allocations(
        GetAllocationsInput(
            customer_id=customer_id,
        )
    )

    assert len(result) == 2

    assert isinstance(result[0], AllocationToolOutput)
    assert result[0].customer_id == customer_id
    assert result[0].gpu_type == "H100"
    assert result[0].gpu_count == 8
    assert result[0].region == "us-east"
    assert result[0].status == "active"

    assert result[1].gpu_type == "A100"
    assert result[1].gpu_count == 16
    assert result[1].region == "eu-west"

    allocation_service.list_customer_allocations.assert_awaited_once_with(
        customer_id,
    )


@pytest.mark.asyncio
async def test_get_allocations_returns_empty_list(
    allocation_tool,
    allocation_service,
):
    customer_id = uuid4()

    allocation_service.list_customer_allocations = AsyncMock(
        return_value=[],
    )

    result = await allocation_tool.get_allocations(
        GetAllocationsInput(
            customer_id=customer_id,
        )
    )

    assert result == []


@pytest.mark.asyncio
async def test_get_allocations_translates_missing_customer(
    allocation_tool,
    allocation_service,
):
    from apps.gpuaas.app.services.allocation import (
        CustomerNotFoundError,
    )

    customer_id = uuid4()

    allocation_service.list_customer_allocations = AsyncMock(
        side_effect=CustomerNotFoundError(
            "Customer not found",
        ),
    )

    with pytest.raises(AllocationCustomerNotFoundError):
        await allocation_tool.get_allocations(
            GetAllocationsInput(
                customer_id=customer_id,
            )
        )


def test_get_allocations_input_rejects_invalid_uuid():
    with pytest.raises(ValueError):
        GetAllocationsInput(
            customer_id="not-a-uuid",
        )
