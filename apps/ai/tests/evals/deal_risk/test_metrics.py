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
    risk_level_points = (
        30.0
        if risk_level_correct
        else 0.0
    )

    score_range_points = (
        20.0
        if score_within_range
        else 0.0
    )

    signal_coverage_points = (
        20.0
        if required_signals_present
        else 0.0
    )

    unsupported_claim_points = (
        10.0
        if forbidden_claims_absent
        else 0.0
    )

    recommended_action_points = (
        20.0
        if recommended_action_correct
        else 0.0
    )

    total_score = (
        risk_level_points
        + score_range_points
        + signal_coverage_points
        + unsupported_claim_points
        + recommended_action_points
    )

    if total_score >= 90:
        rating = "excellent"
    elif total_score >= 75:
        rating = "good"
    elif total_score >= 60:
        rating = "acceptable"
    else:
        rating = "needs_work"

    return DealRiskEvaluation(
        case_id="test",
        schema_valid=True,
        risk_level_correct=risk_level_correct,
        risk_level_points=risk_level_points,
        score_within_range=score_within_range,
        score_range_points=score_range_points,
        required_signals_present=required_signals_present,
        signal_coverage_points=signal_coverage_points,
        forbidden_claims_absent=forbidden_claims_absent,
        unsupported_claim_points=unsupported_claim_points,
        recommended_action_correct=recommended_action_correct,
        recommended_action_points=recommended_action_points,
        canonical_recommended_action=(
            "progress"
            if recommended_action_correct
            else None
        ),
        total_score=total_score,
        rating=rating,
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

    summary = summarize_evaluations(
        evaluations,
    )

    assert summary.total_cases == 4
    assert summary.passed_cases == 1
    assert summary.failed_cases == 3

    assert summary.pass_rate == 25.0
    assert summary.risk_level_accuracy == 75.0
    assert summary.score_range_accuracy == 75.0
    assert summary.signal_coverage_rate == 75.0
    assert summary.forbidden_claim_rate == 100.0
    assert summary.recommended_action_accuracy == 75.0


def test_empty_evaluations_are_supported():
    summary = summarize_evaluations([])

    assert summary.total_cases == 0
    assert summary.passed_cases == 0
    assert summary.failed_cases == 0
    assert summary.pass_rate == 0.0
