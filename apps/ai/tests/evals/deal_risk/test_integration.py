from datetime import date
from unittest.mock import AsyncMock, Mock
from uuid import UUID
from pathlib import Path

import pytest

from apps.ai.agents.deal_risk import DealRiskAgent, DealRiskResult
from apps.ai.evals.deal_risk.dataset import load_deal_risk_eval_dataset
from apps.ai.evals.deal_risk.evaluator import evaluate_deal_risk_result


DATASET = Path("apps/ai/evals/deal_risk/cases.json")


class FakeEvidenceCollector:
    def __init__(
        self,
        evidence,
        *,
        today: date,
    ):
        self.evidence = evidence
        self.today = today

    async def collect(
        self,
        *,
        deal_id,
        organization_id,
        customer_id,
        today,
    ):
        evidence = dict(self.evidence)

        deal = dict(evidence.get("deal", {}))
        crm = dict(evidence.get("crm", {}))

        deal_age_days = deal.get("age_days")
        stage_age_days = deal.get("stage_age_days")

        if deal_age_days is not None:
            from datetime import timedelta

            deal["created_at"] = (
                today - timedelta(days=deal_age_days)
            ).isoformat()

        if stage_age_days is not None:
            from datetime import timedelta

            evidence["stage_entered_at"] = (
                today - timedelta(days=stage_age_days)
            ).isoformat()

        if crm.get("days_since_last_activity") is not None:
            from datetime import timedelta

            evidence["last_activity_at"] = (
                today
                - timedelta(
                    days=crm["days_since_last_activity"],
                )
            ).isoformat()
        else:
            evidence["last_activity_at"] = None

        evidence["deal"] = deal

        evidence["usage"] = {
            "summary": evidence.get(
                "usage",
                {},
            )
        }

        billing = evidence.get("billing")

        if billing is None:
            evidence["billing"] = {
                "spend_growth_30d_percent": None,
            }

        return evidence

@pytest.mark.asyncio
async def test_eval_case_can_run_through_full_agent_pipeline():
    dataset = load_deal_risk_eval_dataset(
        DATASET,
    )

    case = dataset.cases[0]

    llm = AsyncMock()
    llm.generate.return_value = type(
        "Response",
        (),
        {
            "content": (
                '{"risk_score": 10,'
                '"risk_level": "low",'
                '"signals": ["usage_growth", '
                '"economic_buyer_engaged"],'
                '"questions_to_probe": [],'
                '"recommended_action": "progress"}'
            ),
        },
    )()

    signal_engine = Mock()
    signal_engine.evaluate.return_value = type(
        "Signals",
        (),
        {
            "deal_age_days": 24,
            "stage_age_days": 8,
            "days_since_last_activity": 3,
            "usage_declining": False,
            "jobs_unhealthy": False,
            "spend_declining": False,
            "signals": [
                "usage_growth",
                "economic_buyer_engaged",
            ],
        },
    )()

    scorer = Mock()
    scorer.score.return_value = type(
        "RiskScore",
        (),
        {
            "score": 10,
            "level": "low",
        },
    )()

    agent = DealRiskAgent(
        llm=llm,
        evidence_collector=FakeEvidenceCollector(
            case.evidence,
            today=dataset.runner_config.today,
        ),
        signal_engine=signal_engine,
        scorer=scorer,
    )

    result = await agent.analyze(
        deal_id=456,
        organization_id=123,
        customer_id=UUID(
            "00000000-0000-0000-0000-000000000001",
        ),
        today=date(2026, 8, 16),
    )

    evaluation = evaluate_deal_risk_result(
        case,
        result,
    )

    assert isinstance(
        result,
        DealRiskResult,
    )

    assert evaluation.passed is True
