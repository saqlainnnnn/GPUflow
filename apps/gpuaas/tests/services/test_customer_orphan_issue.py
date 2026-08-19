from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.models.customer_data_quality_issue import (
    CustomerDataQualityIssue,
)
from apps.gpuaas.app.services.customer_orphan_issue import (
    CustomerOrphanIssueService,
)


def build_service():
    repository = AsyncMock()

    return (
        CustomerOrphanIssueService(
            repository=repository,
        ),
        repository,
    )


@pytest.mark.asyncio
async def test_open_orphan_creates_new_issue():
    service, repository = build_service()

    repository.find_by_identity.return_value = None

    created = CustomerDataQualityIssue(
        issue_type="orphaned_source",
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        status="open",
        details={
            "reason": "no_customer_identity",
        },
    )

    repository.create.return_value = created

    result = await service.open_orphan(
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    assert result is created

    repository.find_by_identity.assert_awaited_once_with(
        issue_type="orphaned_source",
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    repository.create.assert_awaited_once()

    issue = repository.create.await_args.args[0]

    assert isinstance(issue, CustomerDataQualityIssue)
    assert issue.issue_type == "orphaned_source"
    assert issue.source == "pipedrive"
    assert issue.entity_type == "organization"
    assert issue.external_id == "12345"
    assert issue.status == "open"


@pytest.mark.asyncio
async def test_open_orphan_returns_existing_open_issue():
    service, repository = build_service()

    existing = CustomerDataQualityIssue(
        issue_type="orphaned_source",
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        status="open",
        details={},
    )

    repository.find_by_identity.return_value = existing

    result = await service.open_orphan(
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    assert result is existing
    repository.create.assert_not_awaited()
    repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_open_orphan_reopens_resolved_issue():
    service, repository = build_service()

    existing = CustomerDataQualityIssue(
        issue_type="orphaned_source",
        source="xero",
        entity_type="contact",
        external_id="contact-123",
        status="resolved",
        details={
            "reason": "previously_orphaned",
        },
        resolved_at=datetime.now(timezone.utc),
    )

    repository.find_by_identity.return_value = existing
    repository.update.return_value = existing

    result = await service.open_orphan(
        source="xero",
        entity_type="contact",
        external_id="contact-123",
    )

    assert result is existing
    assert existing.status == "open"
    assert existing.resolved_at is None
    assert existing.details["reason"] == "no_customer_identity"

    repository.create.assert_not_awaited()
    repository.update.assert_awaited_once_with(existing)


@pytest.mark.asyncio
async def test_resolve_orphan_updates_open_issue():
    service, repository = build_service()

    issue = CustomerDataQualityIssue(
        issue_type="orphaned_source",
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        status="open",
        details={},
    )

    repository.find_by_identity.return_value = issue
    repository.update.return_value = issue

    result = await service.resolve_orphan(
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    assert result is issue
    assert issue.status == "resolved"
    assert issue.resolved_at is not None
    assert issue.resolved_at.tzinfo == timezone.utc

    repository.update.assert_awaited_once_with(issue)


@pytest.mark.asyncio
async def test_resolve_orphan_is_idempotent():
    service, repository = build_service()

    resolved_at = datetime.now(timezone.utc)

    issue = CustomerDataQualityIssue(
        issue_type="orphaned_source",
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        status="resolved",
        details={},
        resolved_at=resolved_at,
    )

    repository.find_by_identity.return_value = issue

    result = await service.resolve_orphan(
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    assert result is issue
    assert issue.status == "resolved"
    assert issue.resolved_at == resolved_at

    repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_resolve_missing_issue_returns_none():
    service, repository = build_service()

    repository.find_by_identity.return_value = None

    result = await service.resolve_orphan(
        source="xero",
        entity_type="contact",
        external_id="missing",
    )

    assert result is None
    repository.update.assert_not_awaited()
