from datetime import datetime, timezone
from uuid import UUID

from apps.gpuaas.app.models.customer_data_quality_issue import (
    CustomerDataQualityIssue,
)
from apps.gpuaas.app.repositories.customer_data_quality_issue import (
    CustomerDataQualityIssueRepository,
)


class CustomerDuplicateIssueService:
    def __init__(
        self,
        *,
        repository: CustomerDataQualityIssueRepository,
    ) -> None:
        self.repository = repository

    @staticmethod
    def _candidate_key(
        left_id: str,
        right_id: str,
    ) -> tuple[str, str, str]:
        left_id = str(left_id)
        right_id = str(right_id)

        first, second = sorted(
            [left_id, right_id]
        )

        external_id = f"{first}:{second}"

        return (
            left_id,
            right_id,
            external_id,
        )

    async def list_open_duplicate_candidates(
        self,
    ) -> list[CustomerDataQualityIssue]:
        return await self.repository.find_open_issues(
            issue_type="duplicate_candidate",
            source="gpuflow",
            entity_type="customer",
        )

    async def open_candidate(
        self,
        candidate,
    ) -> CustomerDataQualityIssue:
        left_id, right_id, external_id = (
            self._candidate_key(
                candidate.left_id,
                candidate.right_id,
            )
        )

        issue = await self.repository.find_by_identity(
            issue_type="duplicate_candidate",
            source="gpuflow",
            entity_type="customer",
            external_id=external_id,
        )

        details = {
            "right_customer_id": right_id,
            "match_reasons": list(
                candidate.match_reasons
            ),
        }

        if issue is None:
            issue = CustomerDataQualityIssue(
                customer_id=UUID(left_id),
                issue_type="duplicate_candidate",
                source="gpuflow",
                entity_type="customer",
                external_id=external_id,
                status="open",
                details=details,
            )

            return await self.repository.create(issue)

        if issue.status == "resolved":
            issue.status = "open"
            issue.resolved_at = None

        if issue.details != details:
            issue.details = details
            return await self.repository.update(issue)

        return issue

    async def resolve_candidate(
        self,
        candidate,
    ) -> CustomerDataQualityIssue | None:
        _, _, external_id = self._candidate_key(
            candidate.left_id,
            candidate.right_id,
        )

        issue = await self.repository.find_by_identity(
            issue_type="duplicate_candidate",
            source="gpuflow",
            entity_type="customer",
            external_id=external_id,
        )

        if issue is None:
            return None

        if issue.status == "resolved":
            return issue

        issue.status = "resolved"
        issue.resolved_at = datetime.now(
            timezone.utc
        )

        return await self.repository.update(issue)
