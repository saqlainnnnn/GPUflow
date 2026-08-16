from pydantic import BaseModel, ConfigDict

from apps.ai.evals.deal_risk.evaluator import DealRiskEvaluation


class DealRiskEvalSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: float
    risk_level_accuracy: float
    score_range_accuracy: float
    evidence_signal_rate: float
    forbidden_claim_rate: float
    recommended_action_accuracy: float


def summarize_evaluations(
    evaluations: list[DealRiskEvaluation],
) -> DealRiskEvalSummary:
    total = len(evaluations)

    if total == 0:
        return DealRiskEvalSummary(
            total_cases=0,
            passed_cases=0,
            failed_cases=0,
            pass_rate=0.0,
            risk_level_accuracy=0.0,
            score_range_accuracy=0.0,
            evidence_signal_rate=0.0,
            forbidden_claim_rate=0.0,
            recommended_action_accuracy=0.0,
        )

    def percentage(
        predicate,
    ) -> float:
        return round(
            sum(
                1
                for evaluation in evaluations
                if predicate(evaluation)
            )
            / total
            * 100,
            2,
        )

    passed = sum(
        1
        for evaluation in evaluations
        if evaluation.passed
    )

    return DealRiskEvalSummary(
        total_cases=total,
        passed_cases=passed,
        failed_cases=total - passed,
        pass_rate=round(
            passed / total * 100,
            2,
        ),
        risk_level_accuracy=percentage(
            lambda evaluation: evaluation.risk_level_correct,
        ),
        score_range_accuracy=percentage(
            lambda evaluation: evaluation.score_within_range,
        ),
        evidence_signal_rate=percentage(
            lambda evaluation: evaluation.required_signals_present,
        ),
        forbidden_claim_rate=percentage(
            lambda evaluation: evaluation.forbidden_claims_absent,
        ),
        recommended_action_accuracy=percentage(
            lambda evaluation: evaluation.recommended_action_correct,
        ),
    )
