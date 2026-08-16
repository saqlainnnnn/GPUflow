from datetime import date, timedelta
from typing import Any
from uuid import UUID


class ScenarioEvidenceCollector:
    def __init__(
        self,
        evidence: dict[str, Any],
    ) -> None:
        self.evidence = evidence

    async def collect(
        self,
        *,
        deal_id: int,
        organization_id: int,
        customer_id: UUID,
        today: date,
    ) -> dict[str, Any]:
        evidence = dict(self.evidence)

        deal = dict(
            evidence.get("deal", {}),
        )
        crm = dict(
            evidence.get("crm", {}),
        )
        usage = dict(
            evidence.get("usage", {}),
        )
        jobs = dict(
            evidence.get("jobs", {}),
        )

        deal_age_days = deal.get("age_days")

        if deal_age_days is not None:
            deal["created_at"] = (
                today - timedelta(days=deal_age_days)
            ).isoformat()

        stage_age_days = deal.get("stage_age_days")

        if stage_age_days is not None:
            evidence["stage_entered_at"] = (
                today - timedelta(days=stage_age_days)
            ).isoformat()
        else:
            evidence["stage_entered_at"] = None

        days_since_activity = crm.get(
            "days_since_last_activity",
        )

        if days_since_activity is not None:
            evidence["last_activity_at"] = (
                today - timedelta(days=days_since_activity)
            ).isoformat()
        else:
            evidence["last_activity_at"] = None

        evidence["deal"] = deal

        evidence["usage"] = {
            "summary": usage,
        }

        evidence["jobs"] = jobs

        if evidence.get("billing") is None:
            evidence["billing"] = {
                "spend_growth_30d_percent": None,
            }

        return evidence
