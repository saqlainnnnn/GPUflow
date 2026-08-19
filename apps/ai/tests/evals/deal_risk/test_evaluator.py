from apps.ai.agents.deal_risk import DealRiskResult
from apps.ai.evals.deal_risk.cases import (
    DealRiskEvalCase,
    DealRiskEvalExpected,
)
from apps.ai.evals.deal_risk.evaluator import (
    action_points,
    canonicalize_action,
    evaluate_deal_risk_result,
)


def make_case(
    *,
    action: str = "progress",
) -> DealRiskEvalCase:
    return DealRiskEvalCase(
        case_id="DR-TEST",
        description="test case",
        category="healthy",
        evidence={
            "usage": {
                "growth_30d_percent": 30.0,
            },
        },
        expected=DealRiskEvalExpected(
            risk_level="low",
            score_min=0,
            score_max=25,
            recommended_action=action,
        ),
        required_signals=[
            "usage_growth",
        ],
        forbidden_conclusions=[
            "deal is lost",
        ],
    )


def make_result(
    *,
    risk_score: int = 15,
    risk_level: str = "low",
    signals=None,
    questions=None,
    recommended_action: str = "progress",
) -> DealRiskResult:
    if signals is None:
        signals = [
            {
                "name": "usage_growth",
                "severity": "medium",
                "evidence": "usage growth",
            },
        ]

    if questions is None:
        questions = []

    return DealRiskResult(
        risk_score=risk_score,
        risk_level=risk_level,
        signals=signals,
        questions_to_probe=questions,
        recommended_action=recommended_action,
    )


def test_canonicalizes_progress_action():
    assert (
        canonicalize_action(
            "Progress the deal by scheduling a follow-up meeting",
        )
        == "progress"
    )


def test_canonicalizes_monitor_action():
    assert (
        canonicalize_action(
            "Keep the opportunity warm",
        )
        == "monitor"
    )


def test_canonicalizes_investigate_action():
    assert (
        canonicalize_action(
            "Investigate the cause of the inactivity",
        )
        == "investigate"
    )


def test_canonicalizes_requalify_action():
    assert (
        canonicalize_action(
            "Re-qualify the opportunity",
        )
        == "requalify"
    )


def test_canonicalizes_escalate_action():
    assert (
        canonicalize_action(
            "Escalate to the account executive",
        )
        == "escalate"
    )


def test_canonicalizes_protect_value_action():
    assert (
        canonicalize_action(
            "Address pricing and defend ROI",
        )
        == "protect_value"
    )


def test_canonicalizes_qualify_action():
    assert (
        canonicalize_action(
            "Qualify the customer's financial position",
        )
        == "qualify"
    )


def test_exact_action_gets_full_points():
    assert (
        action_points(
            "investigate",
            "investigate",
        )
        == 20.0
    )


def test_adjacent_action_gets_partial_points():
    assert (
        action_points(
            "investigate",
            "requalify",
        )
        == 12.0
    )


def test_broad_action_gets_lower_partial_points():
    assert (
        action_points(
            "investigate",
            "progress",
        )
        == 8.0
    )


def test_incompatible_action_gets_zero_points():
    assert (
        action_points(
            "protect_value",
            "escalate",
        )
        == 0.0
    )


def test_fully_correct_result_scores_excellent():
    case = make_case()

    result = make_result(
        risk_score=15,
        risk_level="low",
        recommended_action="Progress the deal",
    )

    evaluation = evaluate_deal_risk_result(
        case,
        result,
    )

    assert evaluation.total_score == 100.0
    assert evaluation.rating == "excellent"
    assert evaluation.passed is True


def test_adjacent_action_still_scores_well():
    case = make_case(
        action="investigate",
    )

    result = make_result(
        risk_score=15,
        risk_level="low",
        recommended_action=(
            "Re-qualify the opportunity"
        ),
    )

    evaluation = evaluate_deal_risk_result(
        case,
        result,
    )

    assert evaluation.recommended_action_correct is False
    assert evaluation.recommended_action_points == 12.0
    assert evaluation.total_score == 92.0
    assert evaluation.rating == "excellent"
    assert evaluation.passed is True


def test_wrong_risk_level_still_matters():
    case = make_case()

    result = make_result(
        risk_level="high",
    )

    evaluation = evaluate_deal_risk_result(
        case,
        result,
    )

    assert evaluation.risk_level_points == 0.0
    assert evaluation.total_score == 70.0
    assert evaluation.rating == "acceptable"
    assert evaluation.passed is False


def test_score_range_is_weighted():
    case = make_case()

    result = make_result(
        risk_score=80,
    )

    evaluation = evaluate_deal_risk_result(
        case,
        result,
    )

    assert evaluation.score_range_points == 0.0
    assert evaluation.total_score == 80.0
    assert evaluation.rating == "good"
    assert evaluation.passed is True


def test_action_is_semantic_not_exact_string():
    case = make_case(
        action="progress",
    )

    result = make_result(
        recommended_action=(
            "Schedule a call with the economic buyer "
            "to review the deal and move forward"
        ),
    )

    evaluation = evaluate_deal_risk_result(
        case,
        result,
    )

    assert evaluation.recommended_action_correct is True
    assert evaluation.recommended_action_points == 20.0
    assert evaluation.canonical_recommended_action == "progress"


def test_forbidden_claims_are_still_penalized():
    case = make_case()

    result = make_result(
        recommended_action="The deal is lost",
    )

    evaluation = evaluate_deal_risk_result(
        case,
        result,
    )

    assert evaluation.forbidden_claims_absent is False
    assert evaluation.unsupported_claim_points == 0.0


def test_missing_signal_reduces_signal_coverage():
    case = make_case()

    result = make_result(
        signals=[],
    )

    evaluation = evaluate_deal_risk_result(
        case,
        result,
    )

    assert evaluation.required_signals_present is False
    assert evaluation.signal_coverage_points == 0.0
