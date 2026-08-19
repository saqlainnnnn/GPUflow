from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.services.customer_orphan_detection import (
    CustomerOrphanDetectionService,
    OrphanRecord,
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
async def test_source_record_is_not_orphaned_when_identity_exists():
    service, repository = build_service()

    customer_id = uuid4()

    repository.find_by_external_identity.return_value = object()

    result = await service.check_record(
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    assert result is None

    repository.find_by_external_identity.assert_awaited_once_with(
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )


@pytest.mark.asyncio
async def test_source_record_is_orphaned_when_identity_missing():
    service, repository = build_service()

    repository.find_by_external_identity.return_value = None

    result = await service.check_record(
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    assert isinstance(result, OrphanRecord)
    assert result.source == "pipedrive"
    assert result.entity_type == "organization"
    assert result.external_id == "12345"


@pytest.mark.asyncio
async def test_xero_contact_can_be_orphaned():
    service, repository = build_service()

    repository.find_by_external_identity.return_value = None

    result = await service.check_record(
        source="xero",
        entity_type="contact",
        external_id="contact-123",
    )

    assert isinstance(result, OrphanRecord)
    assert result.source == "xero"
    assert result.entity_type == "contact"
    assert result.external_id == "contact-123"
