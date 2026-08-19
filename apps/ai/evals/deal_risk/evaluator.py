from pydantic import BaseModel, ConfigDict

from apps.ai.agents.deal_risk import DealRiskResult
from apps.ai.evals.deal_risk.cases import DealRiskEvalCase


class DealRiskEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str

    schema_valid: bool

    risk_level_correct: bool
    risk_level_points: float

    score_within_range: bool
    score_range_points: float

    required_signals_present: bool
    signal_coverage_points: float

    forbidden_claims_absent: bool
    unsupported_claim_points: float

    recommended_action_correct: bool
    recommended_action_points: float
    canonical_recommended_action: str | None = None

    total_score: float
    rating: str
    passed: bool


ACTION_ALIASES: dict[str, set[str]] = {
    "progress": {
        "progress",
        "advance",
        "move forward",
        "continue",
        "follow up",
        "schedule a call",
        "schedule a meeting",
        "schedule a follow-up meeting",
        "schedule a follow up meeting",
        "engage the customer",
    },
    "monitor": {
        "monitor",
        "keep warm",
        "keep the opportunity warm",
        "periodic check-in",
        "check in",
        "maintain engagement",
        "maintain momentum",
        "proceed with caution",
        "watch closely",
    },
    "investigate": {
        "investigate",
        "understand",
        "assess",
        "discuss concerns",
        "address concerns",
        "identify roadblocks",
        "establish a clear path forward",
        "identify blockers",
        "understand the cause",
        "understand the root cause",
    },
    "requalify": {
        "requalify",
        "re-qualify",
        "reassess",
        "validate the opportunity",
        "revalidate",
        "qualify again",
    },
    "escalate": {
        "escalate",
        "executive attention",
        "urgent intervention",
        "escalate to",
        "prioritize the opportunity",
    },
    "protect_value": {
        "protect value",
        "defend value",
        "defend roi",
        "address pricing",
        "address price",
        "value sell",
        "focus on roi",
        "roi expectations",
        "price concerns",
        "pricing concerns",
        "value perceptions",
    },
    "qualify": {
        "qualify",
        "financial qualification",
        "financially qualify",
        "assess financial",
        "assess viability",
        "financial risk",
        "financial stability",
    },
}


ACTION_COMPATIBILITY: dict[str, dict[str, float]] = {
    "progress": {
        "monitor": 12.0,
        "investigate": 8.0,
    },
    "monitor": {
        "progress": 12.0,
        "investigate": 12.0,
    },
    "investigate": {
        "monitor": 12.0,
        "requalify": 12.0,
        "progress": 8.0,
        "qualify": 8.0,
    },
    "requalify": {
        "investigate": 12.0,
        "escalate": 12.0,
        "qualify": 8.0,
    },
    "escalate": {
        "requalify": 12.0,
        "investigate": 12.0,
    },
    "protect_value": {
        "investigate": 12.0,
        "progress": 8.0,
        "qualify": 8.0,
    },
    "qualify": {
        "investigate": 12.0,
        "requalify": 12.0,
        "protect_value": 8.0,
    },
}


def canonicalize_action(
    action: str,
) -> str | None:
    normalized = action.strip().lower()

    if normalized in ACTION_ALIASES:
        return normalized

    ordered_actions = (
        "protect_value",
        "requalify",
        "escalate",
        "qualify",
        "investigate",
        "monitor",
        "progress",
    )

    for canonical in ordered_actions:
        for alias in ACTION_ALIASES[canonical]:
            if alias in normalized:
                return canonical

    return None


def action_points(
    expected: str,
    actual: str | None,
) -> float:
    if actual is None:
        return 0.0

    if actual == expected:
        return 20.0

    return ACTION_COMPATIBILITY.get(
        expected,
        {},
    ).get(
        actual,
        0.0,
    )


def _evidence_grounding_ratio(
    case: DealRiskEvalCase,
    result: DealRiskResult,
) -> tuple[bool, float]:
    """
    This is now signal coverage, not LLM grounding.

    The DealRiskAgent exposes canonical deterministic signals in
    DealRiskResult.signals. The evaluator checks whether the expected
    domain signals were identified.
    """
    if not case.required_signals:
        return True, 20.0

    output_signals = {
        signal.name.strip().lower()
        for signal in result.signals
    }

    grounded = sum(
        1
        for required_signal in case.required_signals
        if required_signal.strip().lower()
        in output_signals
    )

    ratio = grounded / len(
        case.required_signals,
    )

    return (
        ratio >= 1.0,
        round(
            ratio * 20.0,
            2,
        ),
    )


def _rating(
    score: float,
) -> str:
    if score >= 90:
        return "excellent"

    if score >= 75:
        return "good"

    if score >= 60:
        return "acceptable"

    return "needs_work"


def evaluate_deal_risk_result(
    case: DealRiskEvalCase,
    result: DealRiskResult,
) -> DealRiskEvaluation:
    risk_level_correct = (
        result.risk_level.strip().lower()
        == case.expected.risk_level.strip().lower()
    )

    risk_level_points = (
        30.0
        if risk_level_correct
        else 0.0
    )

    score_within_range = (
        case.expected.score_min
        <= result.risk_score
        <= case.expected.score_max
    )

    score_range_points = (
        20.0
        if score_within_range
        else 0.0
    )

    (
        required_signals_present,
        signal_coverage_points,
    ) = _evidence_grounding_ratio(
        case,
        result,
    )

    output_text = " ".join(
        [
            *(
                f"{signal.name} {signal.evidence}"
                for signal in result.signals
            ),
            *(
                question.question
                for question in result.questions_to_probe
            ),
            result.recommended_action,
        ]
    ).lower()

    forbidden_claims_absent = all(
        forbidden.strip().lower() not in output_text
        for forbidden in case.forbidden_conclusions
    )

    unsupported_claim_points = (
        10.0
        if forbidden_claims_absent
        else 0.0
    )

    canonical_action = canonicalize_action(
        result.recommended_action,
    )

    recommended_action_correct = (
        canonical_action
        == case.expected.recommended_action
    )

    recommended_action_points = action_points(
        case.expected.recommended_action,
        canonical_action,
    )

    total_score = round(
        risk_level_points
        + score_range_points
        + signal_coverage_points
        + unsupported_claim_points
        + recommended_action_points,
        2,
    )

    rating = _rating(
        total_score,
    )

    return DealRiskEvaluation(
        case_id=case.case_id,
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
        canonical_recommended_action=canonical_action,
        total_score=total_score,
        rating=rating,
        passed=total_score >= 75.0,
    )
