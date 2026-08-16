from pydantic import BaseModel, ConfigDict

from apps.ai.agents.deal_risk import DealRiskResult
from apps.ai.evals.deal_risk.cases import DealRiskEvalCase


class DealRiskEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    schema_valid: bool
    risk_level_correct: bool
    score_within_range: bool
    required_signals_present: bool
    forbidden_claims_absent: bool
    recommended_action_correct: bool
    canonical_recommended_action: str | None = None
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
        "re-engage",
    },
    "investigate": {
        "investigate",
        "understand",
        "assess",
        "discuss concerns",
        "address concerns",
        "identify roadblocks",
        "establish a clear path forward",
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
    },
    "protect_value": {
        "protect value",
        "defend value",
        "defend roi",
        "address pricing",
        "address price",
        "value sell",
        "focus on roi",
    },
    "qualify": {
        "qualify",
        "financial qualification",
        "financially qualify",
        "assess financial",
        "assess viability",
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


def evaluate_deal_risk_result(
    case: DealRiskEvalCase,
    result: DealRiskResult,
) -> DealRiskEvaluation:
    signals = set(result.signals)

    required_signals_present = all(
        signal in signals
        for signal in case.required_signals
    )

    output_text = " ".join(
        [
            *result.signals,
            *result.questions_to_probe,
            result.recommended_action,
        ]
    ).lower()

    forbidden_claims_absent = all(
        forbidden.lower() not in output_text
        for forbidden in case.forbidden_conclusions
    )

    risk_level_correct = (
        result.risk_level.lower()
        == case.expected.risk_level.lower()
    )

    score_within_range = (
        case.expected.score_min
        <= result.risk_score
        <= case.expected.score_max
    )

    canonical_action = canonicalize_action(
        result.recommended_action,
    )

    recommended_action_correct = (
        canonical_action
        == case.expected.recommended_action
    )

    passed = all(
        [
            risk_level_correct,
            score_within_range,
            required_signals_present,
            forbidden_claims_absent,
            recommended_action_correct,
        ]
    )

    return DealRiskEvaluation(
        case_id=case.case_id,
        schema_valid=True,
        risk_level_correct=risk_level_correct,
        score_within_range=score_within_range,
        required_signals_present=required_signals_present,
        forbidden_claims_absent=forbidden_claims_absent,
        recommended_action_correct=recommended_action_correct,
        canonical_recommended_action=canonical_action,
        passed=passed,
    )