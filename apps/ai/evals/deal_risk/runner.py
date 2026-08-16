from dataclasses import dataclass
from time import perf_counter

from apps.ai.agents.deal_risk import DealRiskAgent, DealRiskResult
from apps.ai.evals.deal_risk.cases import DealRiskEvalCase
from apps.ai.evals.deal_risk.dataset import (
    DealRiskEvalRunnerConfig,
)
from apps.ai.evals.deal_risk.evaluator import (
    DealRiskEvaluation,
    evaluate_deal_risk_result,
)
from apps.ai.evals.deal_risk.metrics import (
    DealRiskEvalSummary,
    summarize_evaluations,
)


@dataclass(frozen=True)
class DealRiskEvalResult:
    case_id: str
    execution_success: bool
    latency_ms: float
    evaluation: DealRiskEvaluation | None
    result: DealRiskResult | None
    error: str | None


@dataclass(frozen=True)
class DealRiskEvalReport:
    total_cases: int
    results: list[DealRiskEvalResult]
    failed_execution_cases: int
    average_latency_ms: float
    summary: DealRiskEvalSummary


class DealRiskEvalRunner:
    def __init__(
        self,
        *,
        agent: DealRiskAgent,
        config: DealRiskEvalRunnerConfig,
    ) -> None:
        self.agent = agent
        self.config = config

    async def run(
        self,
        cases: list[DealRiskEvalCase],
    ) -> DealRiskEvalReport:
        results: list[DealRiskEvalResult] = []
        evaluations: list[DealRiskEvaluation] = []
        latencies: list[float] = []

        for case in cases:
            started = perf_counter()

            try:
                result = await self.agent.analyze(
                    deal_id=self.config.deal_id,
                    organization_id=self.config.organization_id,
                    customer_id=self.config.customer_id,
                    today=self.config.today,
                )

                latency_ms = round(
                    (perf_counter() - started) * 1000,
                    2,
                )

                evaluation = evaluate_deal_risk_result(
                    case,
                    result,
                )

                evaluations.append(evaluation)
                latencies.append(latency_ms)

                results.append(
                    DealRiskEvalResult(
                        case_id=case.case_id,
                        execution_success=True,
                        latency_ms=latency_ms,
                        evaluation=evaluation,
                        result=result,
                        error=None,
                    )
                )

            except Exception as exc:
                latency_ms = round(
                    (perf_counter() - started) * 1000,
                    2,
                )

                latencies.append(latency_ms)

                results.append(
                    DealRiskEvalResult(
                        case_id=case.case_id,
                        execution_success=False,
                        latency_ms=latency_ms,
                        evaluation=None,
                        result=None,
                        error=str(exc),
                    )
                )

        failed_execution_cases = sum(
            1
            for result in results
            if not result.execution_success
        )

        average_latency_ms = (
            round(
                sum(latencies) / len(latencies),
                2,
            )
            if latencies
            else 0.0
        )

        return DealRiskEvalReport(
            total_cases=len(cases),
            results=results,
            failed_execution_cases=failed_execution_cases,
            average_latency_ms=average_latency_ms,
            summary=summarize_evaluations(
                evaluations,
            ),
        )
