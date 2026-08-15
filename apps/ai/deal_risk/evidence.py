from datetime import date
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

        failed_jobs = sum(
            1
            for job in jobs
            if self._get_value(job, "status") == "failed"
        )

        total_jobs = len(jobs)

        return {
            "deal": self._serialize(deal),
            "organization": self._serialize(organization),
            "activities": self._serialize(activities),
            "usage": self._serialize(usage),
            "allocations": self._serialize(allocations),
            "jobs": {
                "items": self._serialize(jobs),
                "failed_jobs_30d": failed_jobs,
                "total_jobs_30d": total_jobs,
            },
            "billing": self._serialize(billing),
            "today": today.isoformat(),
        }

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
