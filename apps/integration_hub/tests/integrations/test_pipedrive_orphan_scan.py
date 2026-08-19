from unittest.mock import AsyncMock

import pytest

from apps.integration_hub.app.integrations.pipedrive.orphan_scan import (
    PipedriveOrphanScanner,
)


@pytest.mark.asyncio
async def test_scan_organizations_processes_all_organizations():
    pipedrive = AsyncMock()
    orphan_reconciliation = AsyncMock()

    pipedrive.list_organizations.return_value = [
        {
            "id": 123,
            "name": "Acme AI",
        },
        {
            "id": 456,
            "name": "Beta Compute",
        },
    ]

    scanner = PipedriveOrphanScanner(
        pipedrive=pipedrive,
        orphan_reconciliation=orphan_reconciliation,
    )

    orphan_reconciliation.process_records.return_value = [
        "issue-123",
        None,
    ]

    result = await scanner.scan()

    assert result == [
        "issue-123",
        None,
    ]

    pipedrive.list_organizations.assert_awaited_once()

    orphan_reconciliation.process_records.assert_awaited_once_with(
        [
            {
                "source": "pipedrive",
                "entity_type": "organization",
                "external_id": "123",
            },
            {
                "source": "pipedrive",
                "entity_type": "organization",
                "external_id": "456",
            },
        ]
    )
