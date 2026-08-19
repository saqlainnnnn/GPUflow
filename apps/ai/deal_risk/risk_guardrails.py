from collections.abc import Iterable


MATERIAL_SIGNAL_FLOORS: dict[str, tuple[int, str]] = {
    "build_vs_buy_risk": (60, "medium"),
    "economic_buyer_missing": (40, "medium"),
    "external_blocker": (40, "medium"),
    "price_sensitivity": (40, "medium"),
    "value_risk": (40, "medium"),
    "financial_fragility": (40, "medium"),
    "customer_concentration": (40, "medium"),
    "usage_declining": (40, "medium"),
    "spend_declining": (40, "medium"),
    "job_failures": (40, "medium"),
    "no_recent_activity": (40, "medium"),
    "deal_stale": (40, "medium"),
}


def apply_risk_floor(
    *,
    risk_score: int,
    risk_level: str,
    signals: Iterable[str],
) -> tuple[int, str]:
    normalized_level = risk_level.strip().lower()

    score = risk_score
    level = normalized_level

    signal_set = {
        signal.strip().lower()
        for signal in signals
    }

    for signal, (
        minimum_score,
        minimum_level,
    ) in MATERIAL_SIGNAL_FLOORS.items():
        if signal not in signal_set:
            continue

        if score < minimum_score:
            score = minimum_score

        if (
            minimum_level == "medium"
            and level == "low"
        ):
            level = "medium"

        if (
            minimum_level == "high"
            and level != "high"
        ):
            level = "high"

    # Several compounding operational signals justify
    # a stronger floor than a single isolated signal.
    operational_signals = {
        "usage_declining",
        "job_failures",
        "spend_declining",
        "deal_stale",
        "no_recent_activity",
    }

    operational_count = len(
        signal_set.intersection(
            operational_signals,
        )
    )

    if operational_count >= 3:
        score = max(score, 70)

        if level == "low":
            level = "medium"

    if (
        "build_vs_buy_risk" in signal_set
        and "economic_buyer_missing" in signal_set
    ):
        score = max(score, 60)

        if level == "low":
            level = "medium"

    return (
        min(score, 100),
        level,
    )
