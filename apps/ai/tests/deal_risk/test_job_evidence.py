from datetime import UTC, datetime, timedelta
from unittest.mock import Mock
from uuid import uuid4

from apps.ai.deal_risk.evidence import DealRiskEvidenceCollector


def make_job(
    *,
    created_at: datetime,
    status: str,
):
    return Mock(
        id=uuid4(),
        customer_id=uuid4(),
        status=status,
        failure_reason="OOM" if status == "failed" else None,
        created_at=created_at,
    )


def test_filters_jobs_to_last_30_days():
    today = datetime(
        2026,
        8,
        16,
        tzinfo=UTC,
    )

    jobs = [
        make_job(
            created_at=today - timedelta(days=5),
            status="failed",
        ),
        make_job(
            created_at=today - timedelta(days=20),
            status="completed",
        ),
        make_job(
            created_at=today - timedelta(days=31),
            status="failed",
        ),
    ]

    result = DealRiskEvidenceCollector._calculate_job_metrics(
        jobs,
        today=today.date(),
    )

    assert result == {
        "failed_jobs_30d": 1,
        "total_jobs_30d": 2,
    }


def test_job_exactly_30_days_old_is_included():
    today = datetime(
        2026,
        8,
        16,
        tzinfo=UTC,
    )

    jobs = [
        make_job(
            created_at=today - timedelta(days=30),
            status="failed",
        ),
    ]

    result = DealRiskEvidenceCollector._calculate_job_metrics(
        jobs,
        today=today.date(),
    )

    assert result == {
        "failed_jobs_30d": 1,
        "total_jobs_30d": 1,
    }


def test_no_recent_jobs_returns_zeroes():
    today = datetime(
        2026,
        8,
        16,
        tzinfo=UTC,
    )

    jobs = [
        make_job(
            created_at=today - timedelta(days=31),
            status="failed",
        ),
    ]

    result = DealRiskEvidenceCollector._calculate_job_metrics(
        jobs,
        today=today.date(),
    )

    assert result == {
        "failed_jobs_30d": 0,
        "total_jobs_30d": 0,
    }
