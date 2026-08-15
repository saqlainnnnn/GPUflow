from apps.ai.deal_risk.scoring import (
    DealRiskScorer,
    RiskLevel,
)


def test_high_risk_when_multiple_major_signals_present():
    scorer = DealRiskScorer()

    result = scorer.score(
        signals=[
            "deal_stale",
            "no_recent_activity",
            "usage_declining",
            "job_failures",
            "spend_declining",
        ]
    )

    assert result.score >= 80
    assert result.level is RiskLevel.HIGH


def test_medium_risk_when_some_signals_present():
    scorer = DealRiskScorer()

    result = scorer.score(
        signals=[
            "deal_stale",
            "usage_declining",
        ]
    )

    assert 40 <= result.score < 80
    assert result.level is RiskLevel.MEDIUM


def test_low_risk_with_no_negative_signals():
    scorer = DealRiskScorer()

    result = scorer.score(
        signals=[]
    )

    assert result.score < 40
    assert result.level is RiskLevel.LOW


def test_unknown_signals_do_not_crash_or_inflate_score():
    scorer = DealRiskScorer()

    result = scorer.score(
        signals=[
            "some_future_signal",
        ]
    )

    assert result.score == 0
    assert result.level is RiskLevel.LOW


def test_score_is_bounded():
    scorer = DealRiskScorer()

    result = scorer.score(
        signals=[
            "deal_stale",
            "no_recent_activity",
            "usage_declining",
            "job_failures",
            "spend_declining",
            "deal_stale",
            "usage_declining",
        ]
    )

    assert 0 <= result.score <= 100
