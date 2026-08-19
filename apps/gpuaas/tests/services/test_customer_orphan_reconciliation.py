from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.gpuaas.app.services.customer_orphan_reconciliation import (
    CustomerOrphanReconciliationService,
)


def build_service():
    detector = AsyncMock()
    issue_service = AsyncMock()

    service = CustomerOrphanReconciliationService(
        detector=detector,
        issue_service=issue_service,
    )

    return service, detector, issue_service


@pytest.mark.asyncio
async def test_orphaned_record_opens_issue():
    service, detector, issue_service = build_service()

    orphan = MagicMock()
    detector.check_record.return_value = orphan

    issue = MagicMock()
    issue_service.open_orphan.return_value = issue

    result = await service.process_record(
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    assert result is issue

    detector.check_record.assert_awaited_once_with(
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    issue_service.open_orphan.assert_awaited_once_with(
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    issue_service.resolve_orphan.assert_not_awaited()


@pytest.mark.asyncio
async def test_non_orphaned_record_resolves_existing_issue():
    service, detector, issue_service = build_service()

    detector.check_record.return_value = None

    resolved = MagicMock()
    issue_service.resolve_orphan.return_value = resolved

    result = await service.process_record(
        source="xero",
        entity_type="contact",
        external_id="contact-123",
    )

    assert result is resolved

    detector.check_record.assert_awaited_once_with(
        source="xero",
        entity_type="contact",
        external_id="contact-123",
    )

    issue_service.resolve_orphan.assert_awaited_once_with(
        source="xero",
        entity_type="contact",
        external_id="contact-123",
    )

    issue_service.open_orphan.assert_not_awaited()


@pytest.mark.asyncio
async def test_batch_processes_all_records():
    service, detector, issue_service = build_service()

    detector.check_record.side_effect = [
        MagicMock(),
        None,
        MagicMock(),
    ]

    issue_service.open_orphan.side_effect = [
        "issue-1",
        "issue-3",
    ]

    issue_service.resolve_orphan.return_value = None

    records = [
        {
            "source": "pipedrive",
            "entity_type": "organization",
            "external_id": "100",
        },
        {
            "source": "pipedrive",
            "entity_type": "organization",
            "external_id": "101",
        },
        {
            "source": "xero",
            "entity_type": "contact",
            "external_id": "200",
        },
    ]

    result = await service.process_records(records)

    assert result == [
        "issue-1",
        None,
        "issue-3",
    ]

    assert detector.check_record.await_count == 3
    assert issue_service.open_orphan.await_count == 2
    assert issue_service.resolve_orphan.await_count == 1
