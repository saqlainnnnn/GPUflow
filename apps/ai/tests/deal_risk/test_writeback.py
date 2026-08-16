from unittest.mock import AsyncMock

import pytest

from apps.ai.agents.deal_risk import DealRiskResult
from apps.ai.deal_risk.writeback import DealRiskWriteback


@pytest.fixture
def pipedrive():
    return AsyncMock()

@pytest.mark.asyncio
async def test_writeback_updates_pipedrive_deal():
    pipedrive = AsyncMock()

    result = DealRiskResult(
        risk_score=82,
        risk_level="high",
        signals=[
            "usage_declining",
            "job_failures",
        ],
        questions_to_probe=[
            "What changed in the expansion plan?",
        ],
        recommended_action="Escalate to the account owner.",
    )

    writer = DealRiskWriteback(
        pipedrive_client=pipedrive,
        risk_score_field="custom_risk_score",
        risk_level_field="custom_risk_level",
        signals_field="custom_risk_signals",
        recommendation_field="custom_risk_recommendation",
    )

    await writer.write(
        deal_id=456,
        result=result,
    )

    pipedrive.update_deal.assert_awaited_once_with(
        456,
        fields={
            "custom_risk_score": 82,
            "custom_risk_level": "high",
            "custom_risk_signals": "usage_declining, job_failures",
            "custom_risk_recommendation": (
                "Escalate to the account owner."
            ),
        },
    )


@pytest.mark.asyncio
async def test_writeback_rejects_missing_field_configuration():
    with pytest.raises(ValueError):
        DealRiskWriteback(
            pipedrive_client=AsyncMock(),
            risk_score_field="",
            risk_level_field="custom_risk_level",
            signals_field="custom_risk_signals",
            recommendation_field="custom_risk_recommendation",
        )


@pytest.mark.asyncio
async def test_writeback_passes_custom_fields_to_pipedrive(
    pipedrive,
):
    result = DealRiskResult(
        risk_score=55,
        risk_level="medium",
        signals=["stale_deal"],
        questions_to_probe=[],
        recommended_action="Follow up with the customer.",
    )

    writer = DealRiskWriteback(
        pipedrive_client=pipedrive,
        risk_score_field="risk_score",
        risk_level_field="risk_level",
        signals_field="risk_signals",
        recommendation_field="risk_recommendation",
    )

    await writer.write(
        deal_id=789,
        result=result,
    )

    pipedrive.update_deal.assert_awaited_once_with(
        789,
        fields={
            "risk_score": 55,
            "risk_level": "medium",
            "risk_signals": "stale_deal",
            "risk_recommendation": "Follow up with the customer.",
        },
    )
