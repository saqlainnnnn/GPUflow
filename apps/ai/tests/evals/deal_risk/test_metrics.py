from apps.ai.evals.deal_risk.evaluator import DealRiskEvaluation
from apps.ai.evals.deal_risk.metrics import summarize_evaluations


def evaluation(
    *,
    passed: bool,
    risk_level_correct: bool = True,
    score_within_range: bool = True,
    required_signals_present: bool = True,
    forbidden_claims_absent: bool = True,
    recommended_action_correct: bool = True,
) -> DealRiskEvaluation:
    return DealRiskEvaluation(
        case_id="test",
        schema_valid=True,
        risk_level_correct=risk_level_correct,
        score_within_range=score_within_range,
        required_signals_present=required_signals_present,
        forbidden_claims_absent=forbidden_claims_absent,
        recommended_action_correct=recommended_action_correct,
        passed=passed,
    )


def test_summarize_evaluations():
    evaluations = [
        evaluation(passed=True),
        evaluation(
            passed=False,
            risk_level_correct=False,
        ),
        evaluation(
            passed=False,
            score_within_range=False,
        ),
        evaluation(
            passed=False,
            required_signals_present=False,
            recommended_action_correct=False,
        ),
    ]

    summary = summarize_evaluations(evaluations)

    assert summary.total_cases == 4
    assert summary.passed_cases == 1
    assert summary.failed_cases == 3

    assert summary.pass_rate == 25.0
    assert summary.risk_level_accuracy == 75.0
    assert summary.score_range_accuracy == 75.0
    assert summary.evidence_signal_rate == 75.0
    assert summary.forbidden_claim_rate == 100.0
    assert summary.recommended_action_accuracy == 75.0


def test_empty_evaluations_are_supported():
    summary = summarize_evaluations([])

    assert summary.total_cases == 0
    assert summary.passed_cases == 0
    assert summary.failed_cases == 0
    assert summary.pass_rate == 0.0
