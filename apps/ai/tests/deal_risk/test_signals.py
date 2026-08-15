from datetime import date

import pytest

from apps.ai.deal_risk.signals import (
    DealRiskSignalEngine,
    DealRiskSignalInput,
)


def test_high_risk_signals_for_stale_deal_and_declining_usage():
    engine = DealRiskSignalEngine()

    result = engine.evaluate(
        DealRiskSignalInput(
            deal_created_at=date(2026, 6, 1),
            stage_entered_at=date(2026, 7, 1),
            last_activity_at=date(2026, 8, 1),
            usage_growth_7d_percent=-35.0,
            usage_growth_30d_percent=-42.0,
            failed_jobs_30d=8,
            total_jobs_30d=20,
            spend_growth_30d_percent=-30.0,
            today=date(2026, 8, 16),
        )
    )

    assert result.deal_age_days == 76
    assert result.stage_age_days == 46
    assert result.days_since_last_activity == 15

    assert result.usage_declining is True
    assert result.jobs_unhealthy is True
    assert result.spend_declining is True

    assert "deal_stale" in result.signals
    assert "no_recent_activity" in result.signals
    assert "usage_declining" in result.signals
    assert "job_failures" in result.signals
    assert "spend_declining" in result.signals


def test_healthy_deal_produces_no_negative_signals():
    engine = DealRiskSignalEngine()

    result = engine.evaluate(
        DealRiskSignalInput(
            deal_created_at=date(2026, 8, 1),
            stage_entered_at=date(2026, 8, 10),
            last_activity_at=date(2026, 8, 15),
            usage_growth_7d_percent=25.0,
            usage_growth_30d_percent=40.0,
            failed_jobs_30d=1,
            total_jobs_30d=25,
            spend_growth_30d_percent=30.0,
            today=date(2026, 8, 16),
        )
    )

    assert result.deal_age_days == 15
    assert result.stage_age_days == 6
    assert result.days_since_last_activity == 1

    assert result.usage_declining is False
    assert result.jobs_unhealthy is False
    assert result.spend_declining is False

    assert result.signals == []


@pytest.mark.parametrize(
    ("failed_jobs", "total_jobs", "expected"),
    [
        (0, 0, False),
        (1, 10, False),
        (2, 10, False),
        (3, 10, True),
        (8, 20, True),
    ],
)
def test_job_health_uses_failure_rate_threshold(
    failed_jobs,
    total_jobs,
    expected,
):
    engine = DealRiskSignalEngine()

    result = engine.evaluate(
        DealRiskSignalInput(
            deal_created_at=date(2026, 8, 1),
            stage_entered_at=date(2026, 8, 1),
            last_activity_at=date(2026, 8, 15),
            usage_growth_7d_percent=0.0,
            usage_growth_30d_percent=0.0,
            failed_jobs_30d=failed_jobs,
            total_jobs_30d=total_jobs,
            spend_growth_30d_percent=0.0,
            today=date(2026, 8, 16),
        )
    )

    assert result.jobs_unhealthy is expected


def test_missing_optional_signals_do_not_crash():
    engine = DealRiskSignalEngine()

    result = engine.evaluate(
        DealRiskSignalInput(
            deal_created_at=date(2026, 8, 1),
            stage_entered_at=None,
            last_activity_at=None,
            usage_growth_7d_percent=None,
            usage_growth_30d_percent=None,
            failed_jobs_30d=None,
            total_jobs_30d=None,
            spend_growth_30d_percent=None,
            today=date(2026, 8, 16),
        )
    )

    assert result.deal_age_days == 15
    assert result.stage_age_days is None
    assert result.days_since_last_activity is None
    assert result.signals == []
