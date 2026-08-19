from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.models.customer_data_quality_issue import (
    CustomerDataQualityIssue,
)
from apps.gpuaas.app.repositories.customer_data_quality_issue import (
    CustomerDataQualityIssueRepository,
)


def build_repository():
    session = AsyncMock()
    session.add = MagicMock()

    return (
        CustomerDataQualityIssueRepository(session),
        session,
    )


@pytest.mark.asyncio
async def test_find_by_identity_returns_issue():
    repository, session = build_repository()

    issue = CustomerDataQualityIssue(
        issue_type="orphaned_source",
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        status="open",
        details={
            "reason": "no_customer_identity",
        },
    )

    result_proxy = MagicMock()
    result_proxy.scalar_one_or_none.return_value = issue
    session.execute.return_value = result_proxy

    result = await repository.find_by_identity(
        issue_type="orphaned_source",
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    assert result is issue
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_find_by_identity_returns_none_when_missing():
    repository, session = build_repository()

    result_proxy = MagicMock()
    result_proxy.scalar_one_or_none.return_value = None
    session.execute.return_value = result_proxy

    result = await repository.find_by_identity(
        issue_type="orphaned_source",
        source="pipedrive",
        entity_type="organization",
        external_id="missing",
    )

    assert result is None
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_find_open_issues_returns_only_open_issues():
    repository, session = build_repository()

    result_proxy = MagicMock()

    issues = [
        CustomerDataQualityIssue(
            issue_type="orphaned_source",
            source="pipedrive",
            entity_type="organization",
            external_id="12345",
            status="open",
            details={},
        )
    ]

    result_proxy.scalars.return_value.all.return_value = issues
    session.execute.return_value = result_proxy

    result = await repository.find_open_issues()

    assert result == issues
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_persists_issue():
    repository, session = build_repository()

    issue = CustomerDataQualityIssue(
        issue_type="orphaned_source",
        source="xero",
        entity_type="contact",
        external_id="contact-123",
        status="open",
        details={
            "reason": "no_customer_identity",
        },
    )

    result = await repository.create(issue)

    assert result is issue
    session.add.assert_called_once_with(issue)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(issue)


@pytest.mark.asyncio
async def test_update_persists_existing_issue():
    repository, session = build_repository()

    issue = CustomerDataQualityIssue(
        id=uuid4(),
        issue_type="orphaned_source",
        source="xero",
        entity_type="contact",
        external_id="contact-123",
        status="open",
        details={},
    )

    result = await repository.update(issue)

    assert result is issue
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(issue)
