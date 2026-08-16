from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from apps.ai.tools.jobs import (
    JobCustomerNotFoundError,
    JobTool,
)
from apps.ai.tools.schemas import (
    GetJobsInput,
    JobToolOutput,
)


@pytest.mark.asyncio
async def test_get_jobs_returns_structured_output():
    customer_id = uuid4()

    job_service = AsyncMock()

    jobs = [
        type(
            "Job",
            (),
            {
                "id": uuid4(),
                "external_id": "job-001",
                "customer_id": customer_id,
                "allocation_id": uuid4(),
                "gpu_type": "H100",
                "gpu_count": 8,
                "status": "completed",
                "duration_seconds": 3600,
                "failure_reason": None,
            },
        )(),
        type(
            "Job",
            (),
            {
                "id": uuid4(),
                "external_id": "job-002",
                "customer_id": customer_id,
                "allocation_id": uuid4(),
                "gpu_type": "A100",
                "gpu_count": 4,
                "status": "failed",
                "duration_seconds": 0,
                "failure_reason": "OOM",
            },
        )(),
    ]

    job_service.list_customer_jobs.return_value = jobs

    tool = JobTool(job_service)

    result = await tool.get_jobs(
        GetJobsInput(
            customer_id=customer_id,
        )
    )

    assert len(result) == 2

    assert isinstance(result[0], JobToolOutput)
    assert result[0].external_id == "job-001"
    assert result[0].gpu_type == "H100"
    assert result[0].gpu_count == 8
    assert result[0].status == "completed"

    assert result[1].status == "failed"
    assert result[1].failure_reason == "OOM"

    job_service.list_customer_jobs.assert_awaited_once_with(
        customer_id,
    )


@pytest.mark.asyncio
async def test_get_jobs_returns_empty_list():
    customer_id = uuid4()

    job_service = AsyncMock()
    job_service.list_customer_jobs.return_value = []

    tool = JobTool(job_service)

    result = await tool.get_jobs(
        GetJobsInput(
            customer_id=customer_id,
        )
    )

    assert result == []


@pytest.mark.asyncio
async def test_get_jobs_translates_missing_customer():
    from apps.gpuaas.app.services.job import CustomerNotFoundError

    customer_id = uuid4()

    job_service = AsyncMock()
    job_service.list_customer_jobs.side_effect = CustomerNotFoundError(
        "Customer not found"
    )

    tool = JobTool(job_service)

    with pytest.raises(JobCustomerNotFoundError):
        await tool.get_jobs(
            GetJobsInput(
                customer_id=customer_id,
            )
        )


def test_get_jobs_input_rejects_invalid_uuid():
    with pytest.raises(ValueError):
        GetJobsInput(
            customer_id="not-a-uuid",
        )
