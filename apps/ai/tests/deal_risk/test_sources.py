from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from apps.ai.deal_risk.sources import (
    GPUaaSBillingSource,
    GPUaaSJobSource,
)


@pytest.mark.asyncio
async def test_job_source_returns_customer_jobs():
    session = Mock()
    customer_id = uuid4()

    job_service = AsyncMock()

    jobs = [
        Mock(
            id=uuid4(),
            customer_id=customer_id,
            status="failed",
            failure_reason="OOM",
        ),
        Mock(
            id=uuid4(),
            customer_id=customer_id,
            status="completed",
            failure_reason=None,
        ),
    ]

    job_service.list_customer_jobs.return_value = jobs

    source = GPUaaSJobSource(
        session=session,
        job_service=job_service,
    )

    result = await source.get_jobs(
        customer_id=customer_id,
    )

    assert result == jobs

    job_service.list_customer_jobs.assert_awaited_once_with(
        customer_id,
    )


@pytest.mark.asyncio
async def test_billing_source_returns_customer_billing():
    session = Mock()
    billing_service = AsyncMock()

    summary = Mock(
        currency="USD",
        total_gpu_hours=1100.0,
        subtotal="27500.00",
    )

    billing_service.get_customer_billing.return_value = summary

    source = GPUaaSBillingSource(
        session=session,
        billing_service=billing_service,
    )

    customer_id = uuid4()

    result = await source.get_billing(
        customer_id=customer_id,
    )

    assert result is summary

    billing_service.get_customer_billing.assert_awaited_once_with(
        customer_id,
    )


def test_sources_require_services():
    session = Mock()

    with pytest.raises(ValueError):
        GPUaaSJobSource(
            session=session,
            job_service=None,
        )

    with pytest.raises(ValueError):
        GPUaaSBillingSource(
            session=session,
            billing_service=None,
        )
