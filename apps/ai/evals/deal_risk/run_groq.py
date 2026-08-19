import asyncio
import json
from pathlib import Path
from typing import Any

from groq import AsyncGroq

from apps.ai.agents.deal_risk import DealRiskAgent
from apps.ai.core.llm import LLMService
from apps.ai.evals.deal_risk.dataset import (
    load_deal_risk_eval_dataset,
)
from apps.ai.evals.deal_risk.evaluator import (
    evaluate_deal_risk_result,
)
from apps.ai.evals.deal_risk.scenario import (
    ScenarioEvidenceCollector,
)
from apps.ai.providers.groq import GroqProvider
from apps.gpuaas.app.core.config import get_settings


DATASET = Path(
    "apps/ai/evals/deal_risk/cases.json",
)


class BenchmarkTelemetry:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def record(
        self,
        *,
        model: str | None = None,
        prompt_version: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        latency_ms: float,
        success: bool,
        error: str | None = None,
    ) -> None:
        self.events.append(
            {
                "model": model,
                "prompt_version": prompt_version,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "latency_ms": latency_ms,
                "success": success,
                "error": error,
            }
        )


def build_provider() -> GroqProvider:
    settings = get_settings()

    client = AsyncGroq(
        api_key=settings.groq_api_key,
    )

    return GroqProvider(
        client=client,
        model=settings.groq_model,
    )


async def main() -> None:
    settings = get_settings()

    if not settings.groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured",
        )

    dataset = load_deal_risk_eval_dataset(
        DATASET,
    )

    telemetry = BenchmarkTelemetry()

    llm = LLMService(
        build_provider(),
        telemetry=telemetry,
    )

    signal_engine = __import__(
        "apps.ai.deal_risk.signals",
        fromlist=["DealRiskSignalEngine"],
    ).DealRiskSignalEngine()

    scorer = __import__(
        "apps.ai.deal_risk.scoring",
        fromlist=["DealRiskScorer"],
    ).DealRiskScorer()

    case_results: list[dict[str, Any]] = []

    for index, case in enumerate(
        dataset.cases,
        start=1,
    ):
        print(
            f"[{index}/{len(dataset.cases)}] "
            f"{case.case_id} ...",
            flush=True,
        )

        agent = DealRiskAgent(
            llm=llm,
            evidence_collector=ScenarioEvidenceCollector(
                case.evidence,
            ),
            signal_engine=signal_engine,
            scorer=scorer,
        )

        try:
            result = await agent.analyze(
                deal_id=dataset.runner_config.deal_id,
                organization_id=(
                    dataset.runner_config.organization_id
                ),
                customer_id=(
                    dataset.runner_config.customer_id
                ),
                today=dataset.runner_config.today,
            )

            evaluation = evaluate_deal_risk_result(
                case,
                result,
            )

            event = telemetry.events[-1]

            case_result = {
                "case_id": case.case_id,
                "description": case.description,
                "expected": {
                    "risk_level": case.expected.risk_level,
                    "score_min": case.expected.score_min,
                    "score_max": case.expected.score_max,
                    "recommended_action": (
                        case.expected.recommended_action
                    ),
                },
                "actual": result.model_dump(),
                "evaluation": evaluation.model_dump(),
                "telemetry": event,
            }

            case_results.append(
                case_result,
            )

            print(
                f"  risk={result.risk_level} "
                f"score={result.risk_score} "
                f"quality={evaluation.total_score} "
                f"rating={evaluation.rating} "
                f"action={evaluation.canonical_recommended_action} "
                f"passed={evaluation.passed}",
                flush=True,
            )

        except Exception as exc:
            case_results.append(
                {
                    "case_id": case.case_id,
                    "description": case.description,
                    "execution_success": False,
                    "error": str(exc),
                }
            )

            print(
                f"  ERROR: {exc}",
                flush=True,
            )

    executed_results = [
        result
        for result in case_results
        if result.get("evaluation") is not None
    ]

    evaluations = [
        result["evaluation"]
        for result in executed_results
    ]

    total_cases = len(case_results)
    executed_cases = len(executed_results)

    average_quality = (
        sum(
            evaluation["total_score"]
            for evaluation in evaluations
        )
        / executed_cases
        if executed_cases
        else 0.0
    )

    risk_level_accuracy = (
        sum(
            1
            for evaluation in evaluations
            if evaluation["risk_level_correct"]
        )
        / executed_cases
        * 100
        if executed_cases
        else 0.0
    )

    score_range_accuracy = (
        sum(
            1
            for evaluation in evaluations
            if evaluation["score_within_range"]
        )
        / executed_cases
        * 100
        if executed_cases
        else 0.0
    )

    action_accuracy = (
        sum(
            1
            for evaluation in evaluations
            if evaluation["recommended_action_correct"]
        )
        / executed_cases
        * 100
        if executed_cases
        else 0.0
    )

    grounding_rate = (
        sum(
            evaluation["evidence_grounding_points"] / 20.0
            for evaluation in evaluations
        )
        / executed_cases
        * 100
        if executed_cases
        else 0.0
    )

    unsupported_claim_rate = (
        sum(
            1
            for evaluation in evaluations
            if evaluation["forbidden_claims_absent"]
        )
        / executed_cases
        * 100
        if executed_cases
        else 0.0
    )

    passed_cases = sum(
        1
        for evaluation in evaluations
        if evaluation["passed"]
    )

    successful_telemetry = [
        event
        for event in telemetry.events
        if event["success"]
    ]

    average_latency = (
        sum(
            event["latency_ms"]
            for event in successful_telemetry
        )
        / len(successful_telemetry)
        if successful_telemetry
        else 0.0
    )

    total_input_tokens = sum(
        event["input_tokens"]
        for event in successful_telemetry
    )

    total_output_tokens = sum(
        event["output_tokens"]
        for event in successful_telemetry
    )

    report = {
        "model": settings.groq_model,
        "total_cases": total_cases,
        "executed_cases": executed_cases,
        "passed_cases": passed_cases,
        "pass_rate": round(
            passed_cases / executed_cases * 100,
            2,
        ) if executed_cases else 0.0,
        "average_quality_score": round(
            average_quality,
            2,
        ),
        "risk_level_accuracy": round(
            risk_level_accuracy,
            2,
        ),
        "score_range_accuracy": round(
            score_range_accuracy,
            2,
        ),
        "recommended_action_accuracy": round(
            action_accuracy,
            2,
        ),
        "evidence_grounding_rate": round(
            grounding_rate,
            2,
        ),
        "unsupported_claim_rate": round(
            unsupported_claim_rate,
            2,
        ),
        "average_latency_ms": round(
            average_latency,
            2,
        ),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "cases": case_results,
    }

    output = Path(
        "apps/ai/evals/deal_risk/results.json",
    )

    output.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("Deal Risk Groq Evaluation")
    print("=========================")
    print(f"Model:                  {settings.groq_model}")
    print(f"Cases:                  {total_cases}")
    print(f"Executed:               {executed_cases}")
    print(f"Passed:                 {passed_cases}")
    print(
        f"Pass rate:              {report['pass_rate']}%"
    )
    print(
        f"Average quality:        "
        f"{report['average_quality_score']}"
    )
    print(
        f"Risk accuracy:          "
        f"{report['risk_level_accuracy']}%"
    )
    print(
        f"Score accuracy:         "
        f"{report['score_range_accuracy']}%"
    )
    print(
        f"Action accuracy:        "
        f"{report['recommended_action_accuracy']}%"
    )
    print(
        f"Evidence grounding:    "
        f"{report['evidence_grounding_rate']}%"
    )
    print(
        f"Unsupported claims:    "
        f"{report['unsupported_claim_rate']}%"
    )
    print(
        f"Average latency:        "
        f"{report['average_latency_ms']} ms"
    )
    print(
        f"Input tokens:           "
        f"{total_input_tokens}"
    )
    print(
        f"Output tokens:          "
        f"{total_output_tokens}"
    )
    print()
    print(f"Report: {output}")


if __name__ == "__main__":
    asyncio.run(main())