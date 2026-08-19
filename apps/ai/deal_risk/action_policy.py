from collections.abc import Iterable


def derive_recommended_action(
    *,
    risk_level: str,
    signals: Iterable[str],
) -> str:
    normalized_level = risk_level.strip().lower()

    signal_set = {
        signal.strip().lower()
        for signal in signals
    }

    # Highest-priority business-specific situations first.

    if (
        "build_vs_buy_risk" in signal_set
        and "economic_buyer_missing" in signal_set
        and normalized_level == "high"
    ):
        return "escalate"

    if (
        "financial_fragility" in signal_set
        or "customer_concentration" in signal_set
    ):
        if normalized_level in {"medium", "high"}:
            return "qualify"

    if (
        "price_sensitivity" in signal_set
        or "value_risk" in signal_set
    ):
        return "protect_value"

    if "external_blocker" in signal_set:
        return "monitor"

    if (
        "sovereignty_fit" in signal_set
        and normalized_level == "low"
    ):
        return "progress"

    severe_operational_signals = {
        "usage_declining",
        "job_failures",
        "spend_declining",
        "deal_stale",
        "no_recent_activity",
    }

    severe_count = len(
        signal_set.intersection(
            severe_operational_signals,
        )
    )

    if normalized_level == "high":
        if severe_count >= 2:
            return "requalify"

        if "economic_buyer_missing" in signal_set:
            return "requalify"

        return "investigate"

    if normalized_level == "medium":
        if "economic_buyer_missing" in signal_set:
            return "investigate"

        if severe_count >= 1:
            return "investigate"

        return "monitor"

    # Low risk should normally move the deal forward unless
    # a concrete blocker was detected above.
    return "progress"
