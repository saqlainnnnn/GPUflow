from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DealRiskSignalInput:
    deal_created_at: date
    stage_entered_at: date | None
    last_activity_at: date | None
    usage_growth_7d_percent: float | None
    usage_growth_30d_percent: float | None
    failed_jobs_30d: int | None
    total_jobs_30d: int | None
    spend_growth_30d_percent: float | None
    today: date


@dataclass(frozen=True)
class DealRiskSignals:
    deal_age_days: int
    stage_age_days: int | None
    days_since_last_activity: int | None

    usage_declining: bool
    jobs_unhealthy: bool
    spend_declining: bool

    signals: list[str]


class DealRiskSignalEngine:
    DEAL_STALE_DAYS = 30
    NO_RECENT_ACTIVITY_DAYS = 14
    USAGE_DECLINE_THRESHOLD = -20.0
    SPEND_DECLINE_THRESHOLD = -20.0
    JOB_FAILURE_RATE_THRESHOLD = 0.30

    def evaluate(
        self,
        data: DealRiskSignalInput,
    ) -> DealRiskSignals:
        deal_age_days = (
            data.today - data.deal_created_at
        ).days

        stage_age_days = None

        if data.stage_entered_at is not None:
            stage_age_days = (
                data.today - data.stage_entered_at
            ).days

        days_since_last_activity = None

        if data.last_activity_at is not None:
            days_since_last_activity = (
                data.today - data.last_activity_at
            ).days

        usage_declining = self._usage_declining(data)
        jobs_unhealthy = self._jobs_unhealthy(data)
        spend_declining = self._spend_declining(data)

        signals: list[str] = []

        if deal_age_days >= self.DEAL_STALE_DAYS:
            signals.append("deal_stale")

        if (
            days_since_last_activity is not None
            and days_since_last_activity >= self.NO_RECENT_ACTIVITY_DAYS
        ):
            signals.append("no_recent_activity")

        if usage_declining:
            signals.append("usage_declining")

        if jobs_unhealthy:
            signals.append("job_failures")

        if spend_declining:
            signals.append("spend_declining")

        return DealRiskSignals(
            deal_age_days=deal_age_days,
            stage_age_days=stage_age_days,
            days_since_last_activity=days_since_last_activity,
            usage_declining=usage_declining,
            jobs_unhealthy=jobs_unhealthy,
            spend_declining=spend_declining,
            signals=signals,
        )

    def _usage_declining(
        self,
        data: DealRiskSignalInput,
    ) -> bool:
        if data.usage_growth_7d_percent is not None:
            if (
                data.usage_growth_7d_percent
                <= self.USAGE_DECLINE_THRESHOLD
            ):
                return True

        if data.usage_growth_30d_percent is not None:
            if (
                data.usage_growth_30d_percent
                <= self.USAGE_DECLINE_THRESHOLD
            ):
                return True

        return False

    def _jobs_unhealthy(
        self,
        data: DealRiskSignalInput,
    ) -> bool:
        if (
            data.failed_jobs_30d is None
            or data.total_jobs_30d is None
        ):
            return False

        if data.total_jobs_30d <= 0:
            return False

        failure_rate = (
            data.failed_jobs_30d
            / data.total_jobs_30d
        )

        return (
            failure_rate
            >= self.JOB_FAILURE_RATE_THRESHOLD
        )

    def _spend_declining(
        self,
        data: DealRiskSignalInput,
    ) -> bool:
        if data.spend_growth_30d_percent is None:
            return False

        return (
            data.spend_growth_30d_percent
            <= self.SPEND_DECLINE_THRESHOLD
        )
