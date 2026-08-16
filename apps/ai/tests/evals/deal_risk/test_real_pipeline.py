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
async def test_all_17_cases_run_through_real_signal_and_scoring_layers():
    dataset = load_deal_risk_eval_dataset(
        DATASET,
    )

    signal_engine = DealRiskSignalEngine()
    scorer = DealRiskScorer()

    assert len(dataset.cases) == 17

    results = []

    for case in dataset.cases:
        evidence_collector = ScenarioEvidenceCollector(
            case.evidence,
        )

        llm = AsyncMock()
        llm.generate.return_value = (
            build_neutral_llm_response()
        )

        agent = DealRiskAgent(
            llm=llm,
            evidence_collector=evidence_collector,
            signal_engine=signal_engine,
            scorer=scorer,
        )

        evidence = await evidence_collector.collect(
            deal_id=dataset.runner_config.deal_id,
            organization_id=dataset.runner_config.organization_id,
            customer_id=dataset.runner_config.customer_id,
            today=dataset.runner_config.today,
        )

        signal_input = agent._build_signal_input(
            evidence=evidence,
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

        results.append(
            {
                "case_id": case.case_id,
                "expected_risk": case.expected.risk_level,
                "deterministic_signals": (
                    deterministic_signals.signals
                ),
                "deterministic_score": (
                    deterministic_score.score
                ),
                "llm_risk": result.risk_level,
                "evaluation_passed": evaluation.passed,
            }
        )

    assert len(results) == 17

    for result in results:
        assert "case_id" in result
        assert "deterministic_signals" in result
        assert "deterministic_score" in result