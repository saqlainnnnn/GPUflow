from datetime import date

from apps.ai.deal_risk.signals import (
    DealRiskSignalEngine,
    DealRiskSignalInput,
)


def base_input() -> DealRiskSignalInput:
    return DealRiskSignalInput(
        deal_created_at=date(2026, 7, 1),
        stage_entered_at=date(2026, 7, 20),
        last_activity_at=date(2026, 8, 10),
        usage_growth_7d_percent=10.0,
        usage_growth_30d_percent=15.0,
        failed_jobs_30d=2,
        total_jobs_30d=50,
        spend_growth_30d_percent=12.0,
        today=date(2026, 8, 16),
        technical_champion_engaged=True,
        economic_buyer_engaged=True,
        internal_build_project=False,
        facility_power_ready=True,
        sovereignty_required=False,
        eu_region_required=False,
        air_gapped_requirement=False,
        price_sensitivity=None,
        roi_conversation_completed=False,
        top_customer_revenue_percent=None,
        cash_runway_months=None,
    )


def test_economic_buyer_missing_is_detected():
    data = base_input()
    data = data.__class__(
        **{
            **data.__dict__,
            "economic_buyer_engaged": False,
        }
    )

    result = DealRiskSignalEngine().evaluate(data)

    assert "economic_buyer_missing" in result.signals


def test_build_vs_buy_risk_is_detected():
    data = base_input()
    data = data.__class__(
        **{
            **data.__dict__,
            "internal_build_project": True,
            "technical_champion_engaged": True,
            "economic_buyer_engaged": False,
        }
    )

    result = DealRiskSignalEngine().evaluate(data)

    assert "build_vs_buy_risk" in result.signals


def test_external_blocker_is_detected():
    data = base_input()
    data = data.__class__(
        **{
            **data.__dict__,
            "facility_power_ready": False,
        }
    )

    result = DealRiskSignalEngine().evaluate(data)

    assert "external_blocker" in result.signals


def test_regulatory_tailwind_and_sovereignty_fit_are_detected():
    data = base_input()
    data = data.__class__(
        **{
            **data.__dict__,
            "sovereignty_required": True,
            "eu_region_required": True,
            "air_gapped_requirement": True,
        }
    )

    result = DealRiskSignalEngine().evaluate(data)

    assert "regulatory_tailwind" in result.signals
    assert "sovereignty_fit" in result.signals


def test_price_sensitivity_and_value_risk_are_detected():
    data = base_input()
    data = data.__class__(
        **{
            **data.__dict__,
            "price_sensitivity": "high",
            "roi_conversation_completed": True,
        }
    )

    result = DealRiskSignalEngine().evaluate(data)

    assert "price_sensitivity" in result.signals
    assert "value_risk" in result.signals


def test_financial_fragility_and_customer_concentration_are_detected():
    data = base_input()
    data = data.__class__(
        **{
            **data.__dict__,
            "top_customer_revenue_percent": 78.0,
            "cash_runway_months": 9,
        }
    )

    result = DealRiskSignalEngine().evaluate(data)

    assert "financial_fragility" in result.signals
    assert "customer_concentration" in result.signals


def test_healthy_case_has_no_contextual_risk_signals():
    result = DealRiskSignalEngine().evaluate(
        base_input(),
    )

    assert "economic_buyer_missing" not in result.signals
    assert "build_vs_buy_risk" not in result.signals
    assert "external_blocker" not in result.signals
    assert "regulatory_tailwind" not in result.signals
    assert "price_sensitivity" not in result.signals
    assert "financial_fragility" not in result.signals