from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from apps.ai.deal_risk.evidence import (
    DealRiskEvidenceCollector,
)
from apps.ai.tools.schemas import (
    GetActivitiesInput,
    GetAllocationsInput,
    GetDealInput,
    GetOrganizationInput,
    GetUsageInput,
)


@pytest.mark.asyncio
async def test_collects_deal_risk_evidence():
    customer_id = uuid4()

    deal_tool = AsyncMock()
    crm_tool = AsyncMock()
    usage_tool = AsyncMock()
    allocation_tool = AsyncMock()
    jobs_tool = AsyncMock()
    billing_tool = AsyncMock()

    deal_tool.get_deal.return_value = {
        "id": 456,
        "title": "Acme H100 Expansion",
        "status": "open",
        "value": 125000,
    }

    crm_tool.get_organization.return_value = {
        "id": 123,
        "name": "Acme AI",
    }

    crm_tool.get_activities.return_value = [
        {
            "activity_id": 1001,
            "subject": "Follow up",
            "type": "call",
            "status": "done",
            "due_date": "2026-08-14",
            "done": True,
        }
    ]

    usage_tool.get_usage.return_value = {
        "customer_id": str(customer_id),
        "summary": {
            "gpu_hours_7d": 320.0,
            "gpu_hours_30d": 1100.0,
            "growth_7d_percent": -35.0,
            "growth_30d_percent": -42.0,
        },
    }

    allocation_tool.get_allocations.return_value = [
        {
            "gpu_type": "H100",
            "gpu_count": 8,
            "region": "us-east",
        },
    ]

    jobs_tool.get_jobs.return_value = [
        {
            "id": str(uuid4()),
            "status": "failed",
            "failure_reason": "OOM",
        },
        {
            "id": str(uuid4()),
            "status": "completed",
            "failure_reason": None,
        },
    ]

    billing_tool.get_billing.return_value = {
        "currency": "USD",
        "total_gpu_hours": 1100.0,
        "subtotal": "27500.00",
        "spend_growth_30d_percent": -30.0,
    }

    collector = DealRiskEvidenceCollector(
        deal_tool=deal_tool,
        crm_tool=crm_tool,
        usage_tool=usage_tool,
        allocation_tool=allocation_tool,
        jobs_tool=jobs_tool,
        billing_tool=billing_tool,
    )

    result = await collector.collect(
        deal_id=456,
        organization_id=123,
        customer_id=customer_id,
        today=date(2026, 8, 16),
    )

    assert result["deal"]["id"] == 456
    assert result["organization"]["id"] == 123
    assert result["activities"][0]["activity_id"] == 1001

    assert result["usage"]["summary"]["growth_7d_percent"] == -35.0

    assert result["jobs"]["failed_jobs_30d"] == 1
    assert result["jobs"]["total_jobs_30d"] == 2

    assert result["billing"]["spend_growth_30d_percent"] == -30.0
    assert result["today"] == "2026-08-16"

    deal_tool.get_deal.assert_awaited_once_with(
        deal_id=456,
    )

    crm_tool.get_organization.assert_awaited_once_with(
        organization_id=123,
    )

    crm_tool.get_activities.assert_awaited_once_with(
        deal_id=456,
    )

    usage_tool.get_usage.assert_awaited_once_with(
        customer_id=customer_id,
    )

    allocation_tool.get_allocations.assert_awaited_once_with(
        customer_id=customer_id,
    )

    jobs_tool.get_jobs.assert_awaited_once_with(
        customer_id=customer_id,
    )

    billing_tool.get_billing.assert_awaited_once_with(
        customer_id=customer_id,
    )


@pytest.mark.asyncio
async def test_collector_requires_jobs_source():
    collector = DealRiskEvidenceCollector(
        deal_tool=AsyncMock(),
        crm_tool=AsyncMock(),
        usage_tool=AsyncMock(),
        allocation_tool=AsyncMock(),
        jobs_tool=None,
        billing_tool=AsyncMock(),
    )

    with pytest.raises(ValueError):
        await collector.collect(
            deal_id=456,
            organization_id=123,
            customer_id=uuid4(),
            today=date(2026, 8, 16),
        )


@pytest.mark.asyncio
async def test_collector_requires_billing_source():
    collector = DealRiskEvidenceCollector(
        deal_tool=AsyncMock(),
        crm_tool=AsyncMock(),
        usage_tool=AsyncMock(),
        allocation_tool=AsyncMock(),
        jobs_tool=AsyncMock(),
        billing_tool=None,
    )

    with pytest.raises(ValueError):
        await collector.collect(
            deal_id=456,
            organization_id=123,
            customer_id=uuid4(),
            today=date(2026, 8, 16),
        )
