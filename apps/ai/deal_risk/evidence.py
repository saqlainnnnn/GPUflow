from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID


class JobSource(Protocol):
    async def get_jobs(
        self,
        *,
        customer_id: UUID,
    ) -> list[Any]: ...


class BillingSource(Protocol):
    async def get_billing(
        self,
        *,
        customer_id: UUID,
    ) -> Any: ...


class DealRiskEvidenceCollector:
    def __init__(
        self,
        *,
        deal_tool,
        crm_tool,
        usage_tool,
        allocation_tool,
        jobs_tool: JobSource,
        billing_tool: BillingSource,
    ) -> None:
        self.deal_tool = deal_tool
        self.crm_tool = crm_tool
        self.usage_tool = usage_tool
        self.allocation_tool = allocation_tool
        self.jobs_tool = jobs_tool
        self.billing_tool = billing_tool

    async def collect(
        self,
        *,
        deal_id: int,
        organization_id: int,
        customer_id: UUID,
        today: date,
    ) -> dict[str, Any]:
        if self.jobs_tool is None:
            raise ValueError(
                "Deal risk evidence collector requires jobs_tool",
            )

        if self.billing_tool is None:
            raise ValueError(
                "Deal risk evidence collector requires billing_tool",
            )

        deal = await self.deal_tool.get_deal(
            deal_id=deal_id,
        )

        organization = await self.crm_tool.get_organization(
            organization_id=organization_id,
        )

        activities = await self.crm_tool.get_activities(
            deal_id=deal_id,
        )

        deal_changelog = await self.crm_tool.get_deal_changelog(
            deal_id=deal_id,
        )

        usage = await self.usage_tool.get_usage(
            customer_id=customer_id,
        )

        allocations = await self.allocation_tool.get_allocations(
            customer_id=customer_id,
        )

        jobs = await self.jobs_tool.get_jobs(
            customer_id=customer_id,
        )

        billing = await self.billing_tool.get_billing(
            customer_id=customer_id,
        )

        job_metrics = self._calculate_job_metrics(
            jobs,
            today=today,
        )

        line_items = self._get_value(
            billing,
            "line_items",
        )

        if line_items is None:
            line_items = []

        spend_metrics = self._calculate_spend_metrics(
            line_items,
            today=datetime(
                today.year,
                today.month,
                today.day,
                tzinfo=UTC,
            ),
        )

        current_stage_id = self._get_value(
            deal,
            "stage_id",
        )

        stage_entered_at = self._find_stage_entered_at(
            deal_changelog,
            current_stage_id=current_stage_id,
        )

        last_activity_at = self._find_last_activity_at(
            activities,
        )

        serialized_billing = self._serialize(billing)

        if not isinstance(serialized_billing, dict):
            serialized_billing = {
                "summary": serialized_billing,
            }

        serialized_billing.update(
            {
                "current_30d_spend": str(
                    spend_metrics["current_30d_spend"],
                ),
                "previous_30d_spend": str(
                    spend_metrics["previous_30d_spend"],
                ),
                "spend_growth_30d_percent": (
                    spend_metrics["spend_growth_30d_percent"]
                ),
            }
        )

        return {
            "deal": self._serialize(deal),
            "organization": self._serialize(organization),
            "activities": self._serialize(activities),
            "usage": self._serialize(usage),
            "allocations": self._serialize(allocations),
            "jobs": {
                "items": self._serialize(jobs),
                **job_metrics,
            },
            "billing": serialized_billing,
            "stage_entered_at": stage_entered_at,
            "last_activity_at": last_activity_at,
            "today": today.isoformat(),
        }

    @staticmethod
    def _calculate_job_metrics(
        jobs: list[Any],
        *,
        today: date,
    ) -> dict[str, int]:
        cutoff = today - timedelta(days=30)

        total_jobs = 0
        failed_jobs = 0

        for job in jobs:
            created_at = DealRiskEvidenceCollector._get_value(
                job,
                "created_at",
            )

            if created_at is None:
                continue

            if isinstance(created_at, datetime):
                created_date = created_at.date()
            elif isinstance(created_at, date):
                created_date = created_at
            elif isinstance(created_at, str):
                created_date = date.fromisoformat(
                    created_at[:10],
                )
            else:
                raise ValueError(
                    f"Unsupported job created_at value: {created_at!r}",
                )

            if created_date < cutoff:
                continue

            total_jobs += 1

            if (
                DealRiskEvidenceCollector._get_value(
                    job,
                    "status",
                )
                == "failed"
            ):
                failed_jobs += 1

        return {
            "failed_jobs_30d": failed_jobs,
            "total_jobs_30d": total_jobs,
        }

    @staticmethod
    def _calculate_spend_metrics(
        line_items: list[Any],
        *,
        today: datetime,
    ) -> dict[str, Decimal | float | None]:
        current_start = today - timedelta(days=30)
        previous_start = today - timedelta(days=60)

        current_spend = Decimal("0.00")
        previous_spend = Decimal("0.00")

        for item in line_items:
            timestamp = DealRiskEvidenceCollector._get_value(
                item,
                "timestamp",
            )

            amount = DealRiskEvidenceCollector._get_value(
                item,
                "amount",
            )

            if timestamp is None or amount is None:
                continue

            timestamp = DealRiskEvidenceCollector._parse_datetime(
                timestamp,
            )

            amount = Decimal(str(amount))

            if current_start <= timestamp <= today:
                current_spend += amount
            elif previous_start <= timestamp < current_start:
                previous_spend += amount

        current_spend = current_spend.quantize(Decimal("0.01"))
        previous_spend = previous_spend.quantize(Decimal("0.01"))

        if previous_spend == 0:
            if current_spend == 0:
                growth: float | None = 0.0
            else:
                growth = None
        else:
            growth = round(
                float(
                    (
                        (current_spend - previous_spend)
                        / previous_spend
                    )
                    * Decimal("100")
                ),
                2,
            )

        return {
            "current_30d_spend": current_spend,
            "previous_30d_spend": previous_spend,
            "spend_growth_30d_percent": growth,
        }

    @staticmethod
    def _parse_datetime(
        value: Any,
    ) -> datetime:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(
                    tzinfo=datetime.now().astimezone().tzinfo,
                )

            return value

        if isinstance(value, str):
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00"),
            )

            if parsed.tzinfo is None:
                return parsed.replace(
                    tzinfo=datetime.now().astimezone().tzinfo,
                )

            return parsed

        raise ValueError(
            f"Unsupported datetime value: {value!r}",
        )

    @staticmethod
    def _find_stage_entered_at(
        changelog: list[Any],
        *,
        current_stage_id: int | str | None,
    ) -> str | None:
        if current_stage_id is None:
            return None

        current_stage_id = str(current_stage_id)

        matching_timestamps: list[str] = []

        for change in changelog:
            field_key = DealRiskEvidenceCollector._get_value(
                change,
                "field_key",
            )

            new_value = DealRiskEvidenceCollector._get_value(
                change,
                "new_value",
            )

            timestamp = DealRiskEvidenceCollector._get_value(
                change,
                "timestamp",
            )

            if (
                field_key == "stage_id"
                and new_value is not None
                and str(new_value) == current_stage_id
                and timestamp
            ):
                matching_timestamps.append(
                    str(timestamp),
                )

        if not matching_timestamps:
            return None

        return max(matching_timestamps)

    @staticmethod
    def _find_last_activity_at(
        activities: list[Any],
    ) -> str | None:
        timestamps: list[str] = []

        for activity in activities:
            timestamp = DealRiskEvidenceCollector._get_value(
                activity,
                "updated_at",
            )

            if timestamp:
                timestamps.append(
                    str(timestamp),
                )

        if not timestamps:
            return None

        return max(timestamps)

    @staticmethod
    def _get_value(
        value: Any,
        key: str,
    ) -> Any:
        if isinstance(value, dict):
            return value.get(key)

        return getattr(value, key, None)

    @staticmethod
    def _serialize(value: Any) -> Any:
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")

        if isinstance(value, list):
            return [
                DealRiskEvidenceCollector._serialize(item)
                for item in value
            ]

        if isinstance(value, dict):
            return {
                key: DealRiskEvidenceCollector._serialize(item)
                for key, item in value.items()
            }

        return value
