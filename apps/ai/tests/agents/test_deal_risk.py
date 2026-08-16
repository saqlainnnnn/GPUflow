from datetime import date
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from apps.ai.agents.deal_risk import DealRiskAgent
from apps.ai.core.llm import LLMResponse


def build_signals():
    return type(
        "Signals",
        (),
        {
            "deal_age_days": 76,
            "stage_age_days": 46,
            "days_since_last_activity": 15,
            "usage_declining": True,
            "jobs_unhealthy": True,
            "spend_declining": True,
            "signals": [
                "deal_stale",
                "no_recent_activity",
                "usage_declining",
                "job_failures",
                "spend_declining",
            ],
        },
    )()


def build_risk_score():
    return type(
        "RiskScore",
        (),
        {
            "score": 100,
            "level": "high",
        },
    )()


@pytest.mark.asyncio
async def test_deal_risk_agent_uses_real_evidence_for_signals():
    llm = AsyncMock()
    evidence_collector = AsyncMock()
    signal_engine = Mock()
    scorer = Mock()

    customer_id = uuid4()

    evidence_collector.collect.return_value = {
        "deal": {
            "id": 456,
            "title": "Acme H100 Expansion",
            "created_at": "2026-06-01 10:30:00",
            "stage_id": 7,
        },
        "organization": {
            "id": 123,
            "name": "Acme AI",
        },
        "activities": [
            {
                "activity_id": 1001,
                "updated_at": "2026-08-01 12:00:00",
            }
        ],
        "last_activity_at": "2026-08-01 12:00:00",
        "stage_entered_at": "2026-07-01 12:00:00",
        "usage": {
            "summary": {
                "growth_7d_percent": -35.0,
                "growth_30d_percent": -42.0,
            }
        },
        "jobs": {
            "failed_jobs_30d": 8,
            "total_jobs_30d": 20,
        },
        "billing": {
            "spend_growth_30d_percent": -30.0,
        },
        "today": "2026-08-16",
    }

    signals = build_signals()
    risk_score = build_risk_score()

    signal_engine.evaluate.return_value = signals
    scorer.score.return_value = risk_score

    llm.generate.return_value = LLMResponse(
        content=(
            '{"risk_score": 100,'
            '"risk_level": "high",'
            '"signals": ["usage_declining", "job_failures"],'
            '"questions_to_probe": ["What changed in the expansion plan?"],'
            '"recommended_action": "Escalate to the account owner."}'
        ),
        model="test-model",
        input_tokens=100,
        output_tokens=50,
    )

    agent = DealRiskAgent(
        llm=llm,
        evidence_collector=evidence_collector,
        signal_engine=signal_engine,
        scorer=scorer,
    )

    result = await agent.analyze(
        deal_id=456,
        organization_id=123,
        customer_id=customer_id,
        today=date(2026, 8, 16),
    )

    assert result.risk_score == 100
    assert result.risk_level == "high"

    signal_engine.evaluate.assert_called_once()

    signal_input = signal_engine.evaluate.call_args.args[0]

    assert signal_input.deal_created_at == date(2026, 6, 1)
    assert signal_input.stage_entered_at == date(2026, 7, 1)
    assert signal_input.last_activity_at == date(2026, 8, 1)

    assert signal_input.usage_growth_7d_percent == -35.0
    assert signal_input.usage_growth_30d_percent == -42.0
    assert signal_input.failed_jobs_30d == 8
    assert signal_input.total_jobs_30d == 20
    assert signal_input.spend_growth_30d_percent == -30.0

    scorer.score.assert_called_once_with(
        signals.signals,
    )

    llm.generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_deal_risk_agent_handles_missing_stage_and_activity_dates():
    llm = AsyncMock()
    evidence_collector = AsyncMock()
    signal_engine = Mock()
    scorer = Mock()

    customer_id = uuid4()

    evidence_collector.collect.return_value = {
        "deal": {
            "id": 456,
            "title": "New Deal",
            "created_at": "2026-08-10 10:30:00",
            "stage_id": 7,
        },
        "stage_entered_at": None,
        "last_activity_at": None,
        "usage": {
            "summary": {
                "growth_7d_percent": None,
                "growth_30d_percent": None,
            }
        },
        "jobs": {
            "failed_jobs_30d": 0,
            "total_jobs_30d": 0,
        },
        "billing": {
            "spend_growth_30d_percent": None,
        },
    }

    signal_engine.evaluate.return_value = type(
        "Signals",
        (),
        {
            "deal_age_days": 6,
            "stage_age_days": None,
            "days_since_last_activity": None,
            "usage_declining": False,
            "jobs_unhealthy": False,
            "spend_declining": False,
            "signals": [],
        },
    )()

    scorer.score.return_value = type(
        "RiskScore",
        (),
        {
            "score": 0,
            "level": "low",
        },
    )()

    llm.generate.return_value = LLMResponse(
        content=(
            '{"risk_score": 0,'
            '"risk_level": "low",'
            '"signals": [],'
            '"questions_to_probe": [],'
            '"recommended_action": "Continue monitoring."}'
        ),
        model="test-model",
        input_tokens=50,
        output_tokens=25,
    )

    agent = DealRiskAgent(
        llm=llm,
        evidence_collector=evidence_collector,
        signal_engine=signal_engine,
        scorer=scorer,
    )

    result = await agent.analyze(
        deal_id=456,
        organization_id=123,
        customer_id=customer_id,
        today=date(2026, 8, 16),
    )

    assert result.risk_score == 0

    signal_input = signal_engine.evaluate.call_args.args[0]

    assert signal_input.stage_entered_at is None
    assert signal_input.last_activity_at is None


@pytest.mark.asyncio
async def test_deal_risk_agent_can_write_result_back_to_pipedrive():
    llm = AsyncMock()
    evidence_collector = AsyncMock()
    signal_engine = Mock()
    scorer = Mock()
    writeback = AsyncMock()

    customer_id = uuid4()

    evidence_collector.collect.return_value = {
        "deal": {
            "id": 456,
            "title": "Acme H100 Expansion",
            "created_at": "2026-06-01 10:30:00",
        },
        "stage_entered_at": "2026-07-01 12:00:00",
        "last_activity_at": "2026-08-01 12:00:00",
        "usage": {
            "summary": {
                "growth_7d_percent": -35.0,
                "growth_30d_percent": -42.0,
            }
        },
        "jobs": {
            "failed_jobs_30d": 8,
            "total_jobs_30d": 20,
        },
        "billing": {
            "spend_growth_30d_percent": -30.0,
        },
    }

    signal_engine.evaluate.return_value = build_signals()
    scorer.score.return_value = build_risk_score()

    llm.generate.return_value = LLMResponse(
        content=(
            '{"risk_score": 100,'
            '"risk_level": "high",'
            '"signals": ["usage_declining", "job_failures"],'
            '"questions_to_probe": ["What changed in the expansion plan?"],'
            '"recommended_action": "Escalate to the account owner."}'
        ),
        model="test-model",
        input_tokens=100,
        output_tokens=50,
    )

    agent = DealRiskAgent(
        llm=llm,
        evidence_collector=evidence_collector,
        signal_engine=signal_engine,
        scorer=scorer,
        writeback=writeback,
    )

    result = await agent.analyze(
        deal_id=456,
        organization_id=123,
        customer_id=customer_id,
        today=date(2026, 8, 16),
        writeback=True,
    )

    assert result.risk_score == 100

    writeback.write.assert_awaited_once_with(
        deal_id=456,
        result=result,
    )


@pytest.mark.asyncio
async def test_deal_risk_agent_does_not_write_back_by_default():
    llm = AsyncMock()
    evidence_collector = AsyncMock()
    signal_engine = Mock()
    scorer = Mock()
    writeback = AsyncMock()

    evidence_collector.collect.return_value = {
        "deal": {
            "id": 456,
            "title": "Acme H100 Expansion",
            "created_at": "2026-06-01 10:30:00",
        },
        "stage_entered_at": None,
        "last_activity_at": None,
        "usage": {
            "summary": {
                "growth_7d_percent": 0.0,
                "growth_30d_percent": 0.0,
            }
        },
        "jobs": {
            "failed_jobs_30d": 0,
            "total_jobs_30d": 0,
        },
        "billing": {
            "spend_growth_30d_percent": 0.0,
        },
    }

    signal_engine.evaluate.return_value = type(
        "Signals",
        (),
        {
            "deal_age_days": 10,
            "stage_age_days": None,
            "days_since_last_activity": None,
            "usage_declining": False,
            "jobs_unhealthy": False,
            "spend_declining": False,
            "signals": [],
        },
    )()

    scorer.score.return_value = type(
        "RiskScore",
        (),
        {
            "score": 0,
            "level": "low",
        },
    )()

    llm.generate.return_value = LLMResponse(
        content=(
            '{"risk_score": 0,'
            '"risk_level": "low",'
            '"signals": [],'
            '"questions_to_probe": [],'
            '"recommended_action": "Continue monitoring."}'
        ),
        model="test-model",
        input_tokens=50,
        output_tokens=25,
    )

    agent = DealRiskAgent(
        llm=llm,
        evidence_collector=evidence_collector,
        signal_engine=signal_engine,
        scorer=scorer,
        writeback=writeback,
    )

    await agent.analyze(
        deal_id=456,
        organization_id=123,
        customer_id=uuid4(),
        today=date(2026, 8, 16),
    )

    writeback.write.assert_not_awaited()
