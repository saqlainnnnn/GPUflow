from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from apps.ai.agents.deal_risk import DealRiskResult
from apps.ai.evals.deal_risk.dataset import (
    load_deal_risk_eval_dataset,
)
from apps.ai.evals.deal_risk.runner import (
    DealRiskEvalRunner,
)


DATASET = Path("apps/ai/evals/deal_risk/cases.json")


@pytest.mark.asyncio
async def test_runner_executes_all_dataset_cases():
    dataset = load_deal_risk_eval_dataset(DATASET)

    agent = AsyncMock()

    agent.analyze.return_value = DealRiskResult(
        risk_score=10,
        risk_level="low",
        signals=["usage_growth"],
        questions_to_probe=[],
        recommended_action="progress",
    )

    runner = DealRiskEvalRunner(
        agent=agent,
        config=dataset.runner_config,
    )

    report = await runner.run(
        dataset.cases,
    )

    assert report.total_cases == 17
    assert len(report.results) == 17
    assert agent.analyze.await_count == 17
    assert report.average_latency_ms >= 0


@pytest.mark.asyncio
async def test_runner_records_failed_case():
    dataset = load_deal_risk_eval_dataset(DATASET)

    agent = AsyncMock()
    agent.analyze.side_effect = RuntimeError(
        "LLM unavailable",
    )

    runner = DealRiskEvalRunner(
        agent=agent,
        config=dataset.runner_config,
    )

    report = await runner.run(
        dataset.cases[:1],
    )

    assert report.total_cases == 1
    assert report.failed_execution_cases == 1
    assert report.results[0].execution_success is False
    assert report.results[0].error == "LLM unavailable"
