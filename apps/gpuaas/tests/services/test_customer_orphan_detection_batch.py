from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.services.customer_orphan_detection import (
    CustomerOrphanDetectionService,
)


def build_service():
    repository = AsyncMock()

    return (
        CustomerOrphanDetectionService(
            identity_repository=repository,
        ),
        repository,
    )


@pytest.mark.asyncio
async def test_batch_returns_only_orphaned_records():
    service, repository = build_service()

    repository.find_by_external_identity.side_effect = [
        object(),
        None,
        None,
        object(),
    ]

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
        {
            "source": "xero",
            "entity_type": "contact",
            "external_id": "201",
        },
    ]

    result = await service.check_records(records)

    assert len(result) == 2

    assert result[0].source == "pipedrive"
    assert result[0].external_id == "101"

    assert result[1].source == "xero"
    assert result[1].external_id == "200"

    assert repository.find_by_external_identity.await_count == 4


@pytest.mark.asyncio
async def test_empty_batch_returns_empty_result():
    service, repository = build_service()

    result = await service.check_records([])

    assert result == []
    repository.find_by_external_identity.assert_not_awaited()


@pytest.mark.asyncio
async def test_batch_preserves_input_order():
    service, repository = build_service()

    repository.find_by_external_identity.side_effect = [
        None,
        None,
    ]

    records = [
        {
            "source": "xero",
            "entity_type": "contact",
            "external_id": "xero-1",
        },
        {
            "source": "pipedrive",
            "entity_type": "organization",
            "external_id": "pd-1",
        },
    ]

    result = await service.check_records(records)

    assert [
        (item.source, item.external_id)
        for item in result
    ] == [
        ("xero", "xero-1"),
        ("pipedrive", "pd-1"),
    ]
