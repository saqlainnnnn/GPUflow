from unittest.mock import AsyncMock

import pytest

from apps.gpuaas.app.services.xero_orphan_scan import (
    XeroOrphanScanner,
)


@pytest.mark.asyncio
async def test_scan_contacts_processes_all_contacts():
    xero = AsyncMock()
    orphan_reconciliation = AsyncMock()

    xero.list_contacts.return_value = [
        {
            "ContactID": "contact-123",
            "Name": "Acme AI",
        },
        {
            "ContactID": "contact-456",
            "Name": "Beta Compute",
        },
    ]

    orphan_reconciliation.process_records.return_value = [
        "issue-123",
        None,
    ]

    scanner = XeroOrphanScanner(
        xero=xero,
        orphan_reconciliation=orphan_reconciliation,
    )

    result = await scanner.scan()

    assert result == [
        "issue-123",
        None,
    ]

    xero.list_contacts.assert_awaited_once()

    orphan_reconciliation.process_records.assert_awaited_once_with(
        [
            {
                "source": "xero",
                "entity_type": "contact",
                "external_id": "contact-123",
            },
            {
                "source": "xero",
                "entity_type": "contact",
                "external_id": "contact-456",
            },
        ]
    )


@pytest.mark.asyncio
async def test_scan_empty_xero_contacts():
    xero = AsyncMock()
    orphan_reconciliation = AsyncMock()

    xero.list_contacts.return_value = []

    orphan_reconciliation.process_records.return_value = []

    scanner = XeroOrphanScanner(
        xero=xero,
        orphan_reconciliation=orphan_reconciliation,
    )

    result = await scanner.scan()

    assert result == []

    orphan_reconciliation.process_records.assert_awaited_once_with(
        []
    )
