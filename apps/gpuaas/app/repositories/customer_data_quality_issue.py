from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.customer_data_quality_issue import (
    CustomerDataQualityIssue,
)


class CustomerDataQualityIssueRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def find_by_identity(
        self,
        *,
        issue_type: str,
        source: str,
        entity_type: str,
        external_id: str,
    ) -> CustomerDataQualityIssue | None:
        result = await self.session.execute(
            select(CustomerDataQualityIssue).where(
                CustomerDataQualityIssue.issue_type == issue_type,
                CustomerDataQualityIssue.source == source,
                CustomerDataQualityIssue.entity_type == entity_type,
                CustomerDataQualityIssue.external_id == external_id,
            )
        )

        return result.scalar_one_or_none()

    async def find_open_issues(
        self,
        *,
        issue_type: str | None = None,
        source: str | None = None,
        entity_type: str | None = None,
    ) -> list[CustomerDataQualityIssue]:
        conditions = [
            CustomerDataQualityIssue.status == "open"
        ]

        if issue_type is not None:
            conditions.append(
                CustomerDataQualityIssue.issue_type
                == issue_type
            )

        if source is not None:
            conditions.append(
                CustomerDataQualityIssue.source
                == source
            )

        if entity_type is not None:
            conditions.append(
                CustomerDataQualityIssue.entity_type
                == entity_type
            )

        result = await self.session.execute(
            select(CustomerDataQualityIssue)
            .where(*conditions)
            .order_by(
                CustomerDataQualityIssue.detected_at.desc()
            )
        )

        return list(result.scalars().all())

    async def create(
        self,
        issue: CustomerDataQualityIssue,
    ) -> CustomerDataQualityIssue:
        self.session.add(issue)

        await self.session.flush()
        await self.session.refresh(issue)

        return issue

    async def update(
        self,
        issue: CustomerDataQualityIssue,
    ) -> CustomerDataQualityIssue:
        await self.session.flush()
        await self.session.refresh(issue)

        return issue
