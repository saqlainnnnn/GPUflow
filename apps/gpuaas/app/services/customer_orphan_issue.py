from datetime import datetime, timezone

from apps.gpuaas.app.models.customer_data_quality_issue import (
    CustomerDataQualityIssue,
)
from apps.gpuaas.app.repositories.customer_data_quality_issue import (
    CustomerDataQualityIssueRepository,
)


class CustomerOrphanIssueService:
    def __init__(
        self,
        *,
        repository: CustomerDataQualityIssueRepository,
    ) -> None:
        self.repository = repository

    async def open_orphan(
        self,
        *,
        source: str,
        entity_type: str,
        external_id: str,
    ) -> CustomerDataQualityIssue:
        issue = await self.repository.find_by_identity(
            issue_type="orphaned_source",
            source=source,
            entity_type=entity_type,
            external_id=external_id,
        )

        if issue is None:
            issue = CustomerDataQualityIssue(
                issue_type="orphaned_source",
                source=source,
                entity_type=entity_type,
                external_id=external_id,
                status="open",
                details={
                    "reason": "no_customer_identity",
                },
            )

            return await self.repository.create(issue)

        if issue.status == "resolved":
            issue.status = "open"
            issue.resolved_at = None
            issue.details = {
                "reason": "no_customer_identity",
            }

            return await self.repository.update(issue)

        return issue

    async def resolve_orphan(
        self,
        *,
        source: str,
        entity_type: str,
        external_id: str,
    ) -> CustomerDataQualityIssue | None:
        issue = await self.repository.find_by_identity(
            issue_type="orphaned_source",
            source=source,
            entity_type=entity_type,
            external_id=external_id,
        )

        if issue is None:
            return None

        if issue.status == "resolved":
            return issue

        issue.status = "resolved"
        issue.resolved_at = datetime.now(timezone.utc)

        return await self.repository.update(issue)
