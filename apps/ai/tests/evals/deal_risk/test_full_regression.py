import json
from datetime import timedelta
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from apps.ai.agents.deal_risk import DealRiskAgent
from apps.ai.core.llm import LLMResponse
from apps.ai.deal_risk.scoring import DealRiskScorer
from apps.ai.deal_risk.signals import DealRiskSignalEngine
from apps.ai.evals.deal_risk.dataset import (
    load_deal_risk_eval_dataset,
)
from apps.ai.evals.deal_risk.evaluator import (
    evaluate_deal_risk_result,
)
from apps.ai.evals.deal_risk.scenario import (
    ScenarioEvidenceCollector,
)

DATASET = Path(
    "apps/ai/evals/deal_risk/cases.json",
)





def build_neutral_llm_response() -> LLMResponse:
    return LLMResponse(
        content=json.dumps(
            {
                "risk_score": 50,
                "risk_level": "medium",
                "signals": [],
                "questions_to_probe": [],
                "recommended_action": "investigate",
            }
        ),
        model="eval-model",
        input_tokens=100,
        output_tokens=50,
    )


@pytest.mark.asyncio
async def test_full_regression_runs_all_17_cases():
    dataset = load_deal_risk_eval_dataset(
        DATASET,
    )

    signal_engine = DealRiskSignalEngine()
    scorer = DealRiskScorer()

    assert len(dataset.cases) == 17

    results: list[tuple[str, object]] = []

    for case in dataset.cases:
        evidence = ScenarioEvidenceCollector(
            case.evidence,
        )

        llm = AsyncMock()
        llm.generate.return_value = (
            build_neutral_llm_response()
        )

        agent = DealRiskAgent(
            llm=llm,
            evidence_collector=evidence,
            signal_engine=signal_engine,
            scorer=scorer,
        )

        agent_evidence = await evidence.collect(
            deal_id=dataset.runner_config.deal_id,
            organization_id=dataset.runner_config.organization_id,
            customer_id=dataset.runner_config.customer_id,
            today=dataset.runner_config.today,
        )

        signal_input = agent._build_signal_input(
            evidence=agent_evidence,
            today=dataset.runner_config.today,
        )

        deterministic_signals = signal_engine.evaluate(
            signal_input,
        )

        deterministic_score = scorer.score(
            deterministic_signals.signals,
        )

        result = await agent.analyze(
            deal_id=dataset.runner_config.deal_id,
            organization_id=dataset.runner_config.organization_id,
            customer_id=dataset.runner_config.customer_id,
            today=dataset.runner_config.today,
        )

        evaluation = evaluate_deal_risk_result(
            case,
            result,
        )

        print(
            f"\n{case.case_id}"
            f" | expected={case.expected.risk_level}"
            f" | deterministic={deterministic_signals.signals}"
            f" | deterministic_score={deterministic_score.score}"
            f" | llm={result.risk_level}"
            f" | evaluation={'PASS' if evaluation.passed else 'FAIL'}"
        )

        results.append(
            (
                case.case_id,
                evaluation,
            )
        )

    assert len(results) == 17