from apps.ai.deal_risk.risk_guardrails import apply_risk_floor


def test_low_risk_is_raised_for_financial_fragility():
    score, level = apply_risk_floor(
        risk_score=20,
        risk_level="low",
        signals=["financial_fragility"],
    )

    assert score == 40
    assert level == "medium"


def test_low_risk_is_raised_for_customer_concentration():
    score, level = apply_risk_floor(
        risk_score=10,
        risk_level="low",
        signals=["customer_concentration"],
    )

    assert score == 40
    assert level == "medium"


def test_low_risk_is_raised_for_build_vs_buy():
    score, level = apply_risk_floor(
        risk_score=20,
        risk_level="low",
        signals=["build_vs_buy_risk"],
    )

    assert score == 60
    assert level == "medium"


def test_build_vs_buy_and_missing_buyer_raise_material_floor():
    score, level = apply_risk_floor(
        risk_score=20,
        risk_level="low",
        signals=[
            "build_vs_buy_risk",
            "economic_buyer_missing",
        ],
    )

    assert score == 60
    assert level == "medium"


def test_three_operational_signals_raise_floor():
    score, level = apply_risk_floor(
        risk_score=15,
        risk_level="low",
        signals=[
            "deal_stale",
            "no_recent_activity",
            "job_failures",
        ],
    )

    assert score == 70
    assert level == "medium"


def test_high_risk_is_not_downgraded():
    score, level = apply_risk_floor(
        risk_score=90,
        risk_level="high",
        signals=["price_sensitivity"],
    )

    assert score == 90
    assert level == "high"
