from datetime import UTC, datetime, timedelta
from decimal import Decimal

from apps.ai.deal_risk.evidence import DealRiskEvidenceCollector


def make_line_item(
    *,
    timestamp: datetime,
    amount: str,
):
    return {
        "timestamp": timestamp,
        "amount": Decimal(amount),
    }


def test_calculates_30_day_spend_growth():
    today = datetime(
        2026,
        8,
        16,
        tzinfo=UTC,
    )

    line_items = [
        make_line_item(
            timestamp=today - timedelta(days=5),
            amount="1500.00",
        ),
        make_line_item(
            timestamp=today - timedelta(days=20),
            amount="1000.00",
        ),
        make_line_item(
            timestamp=today - timedelta(days=40),
            amount="2000.00",
        ),
    ]

    result = DealRiskEvidenceCollector._calculate_spend_metrics(
        line_items,
        today=today,
    )

    assert result["current_30d_spend"] == Decimal("2500.00")
    assert result["previous_30d_spend"] == Decimal("2000.00")
    assert result["spend_growth_30d_percent"] == 25.0


def test_zero_previous_spend_with_current_spend_returns_none_growth():
    today = datetime(
        2026,
        8,
        16,
        tzinfo=UTC,
    )

    line_items = [
        make_line_item(
            timestamp=today - timedelta(days=5),
            amount="1000.00",
        ),
    ]

    result = DealRiskEvidenceCollector._calculate_spend_metrics(
        line_items,
        today=today,
    )

    assert result["current_30d_spend"] == Decimal("1000.00")
    assert result["previous_30d_spend"] == Decimal("0.00")
    assert result["spend_growth_30d_percent"] is None


def test_zero_spend_in_both_periods_returns_zero_growth():
    today = datetime(
        2026,
        8,
        16,
        tzinfo=UTC,
    )

    result = DealRiskEvidenceCollector._calculate_spend_metrics(
        [],
        today=today,
    )

    assert result["current_30d_spend"] == Decimal("0.00")
    assert result["previous_30d_spend"] == Decimal("0.00")
    assert result["spend_growth_30d_percent"] == 0.0


def test_exact_30_day_boundary_belongs_to_current_period():
    today = datetime(
        2026,
        8,
        16,
        tzinfo=UTC,
    )

    line_items = [
        make_line_item(
            timestamp=today - timedelta(days=30),
            amount="500.00",
        ),
        make_line_item(
            timestamp=today - timedelta(days=60),
            amount="1000.00",
        ),
    ]

    result = DealRiskEvidenceCollector._calculate_spend_metrics(
        line_items,
        today=today,
    )

    assert result["current_30d_spend"] == Decimal("500.00")
    assert result["previous_30d_spend"] == Decimal("1000.00")
    assert result["spend_growth_30d_percent"] == -50.0
