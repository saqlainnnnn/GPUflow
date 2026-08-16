from apps.ai.agents.deal_risk import DealRiskResult
from apps.ai.evals.deal_risk.cases import (
    DealRiskEvalCase,
    DealRiskEvalExpected,
)
from apps.ai.evals.deal_risk.evaluator import (
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
    signals: list[str] | None = None,
    recommended_action: str = "progress",
) -> DealRiskResult:
    if signals is None:
        signals = ["usage_growth"]

    return DealRiskResult(
        risk_score=risk_score,
        risk_level=risk_level,
        signals=signals,
        questions_to_probe=[],
        recommended_action=recommended_action,
    )


def test_canonicalizes_progress_actions():
    assert (
        canonicalize_action(
            "Schedule a follow-up meeting",
        )
        == "progress"
    )


def test_canonicalizes_monitor_actions():
    assert (
        canonicalize_action(
            "Keep the opportunity warm",
        )
        == "monitor"
    )


def test_canonicalizes_investigate_actions():
    assert (
        canonicalize_action(
            "Discuss concerns and establish a clear path forward",
        )
        == "investigate"
    )


def test_canonicalizes_requalify_actions():
    assert (
        canonicalize_action(
            "Re-qualify the opportunity",
        )
        == "requalify"
    )


def test_canonicalizes_escalate_actions():
    assert (
        canonicalize_action(
            "Escalate to the account executive",
        )
        == "escalate"
    )


def test_canonicalizes_protect_value_actions():
    assert (
        canonicalize_action(
            "Address pricing and defend ROI",
        )
        == "protect_value"
    )


def test_evaluator_accepts_natural_language_progress_action():
    case = make_case()

    result = make_result(
        recommended_action=(
            "Schedule a call to discuss the customer's progress"
        ),
    )

    evaluation = evaluate_deal_risk_result(
        case,
        result,
    )

    assert evaluation.recommended_action_correct is True
    assert evaluation.canonical_recommended_action == "progress"
    assert evaluation.passed is True


def test_evaluator_rejects_wrong_risk_level():
    case = make_case()

    result = make_result(
        risk_level="high",
    )

    evaluation = evaluate_deal_risk_result(
        case,
        result,
    )

    assert evaluation.risk_level_correct is False
    assert evaluation.passed is False


def test_evaluator_rejects_score_outside_expected_range():
    case = make_case()

    result = make_result(
        risk_score=80,
    )

    evaluation = evaluate_deal_risk_result(
        case,
        result,
    )

    assert evaluation.score_within_range is False
    assert evaluation.passed is False


def test_evaluator_requires_expected_signals():
    case = make_case()

    result = make_result(
        signals=[],
    )

    evaluation = evaluate_deal_risk_result(
        case,
        result,
    )

    assert evaluation.required_signals_present is False
    assert evaluation.passed is False


def test_evaluator_detects_forbidden_conclusions():
    case = make_case()

    result = make_result(
        recommended_action="deal is lost",
    )

    evaluation = evaluate_deal_risk_result(
        case,
        result,
    )

    assert evaluation.forbidden_claims_absent is False
    assert evaluation.passed is False