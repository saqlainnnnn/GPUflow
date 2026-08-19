from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.models.customer_data_quality import (
    CustomerDataQualityRecord,
)
from apps.gpuaas.app.services.customer_data_quality_persistence import (
    CustomerDataQualityPersistenceService,
)


def build_service():
    repository = AsyncMock()

    service = CustomerDataQualityPersistenceService(
        repository=repository,
    )

    return service, repository


def build_result(
    *,
    source="pipedrive",
    entity_type="organization",
    status="matched",
    mismatches=None,
    missing=None,
    fields=None,
):
    result = MagicMock()

    result.source = source
    result.entity_type = entity_type
    result.status.value = status
    result.mismatches = mismatches or []
    result.missing = missing or []
    result.fields = fields or {}

    return result


@pytest.mark.asyncio
async def test_persist_creates_new_record():
    service, repository = build_service()

    customer_id = uuid4()

    repository.find_for_identity.return_value = None

    created_record = MagicMock()
    repository.create.return_value = created_record

    result = build_result(
        status="matched",
        fields={
            "company_name": {
                "status": "match",
            }
        },
    )

    persisted = await service.persist(
        customer_id=customer_id,
        external_id="12345",
        reconciliation=result,
    )

    assert persisted is created_record

    repository.find_for_identity.assert_awaited_once_with(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    repository.create.assert_awaited_once()

    created = repository.create.await_args.args[0]

    assert isinstance(
        created,
        CustomerDataQualityRecord,
    )

    assert created.customer_id == customer_id
    assert created.source == "pipedrive"
    assert created.entity_type == "organization"
    assert created.external_id == "12345"
    assert created.status == "matched"
    assert created.mismatches == []
    assert created.missing == []
    assert created.fields == {
        "company_name": {
            "status": "match",
            "canonical_value": None,
            "source_value": None,
        }
    }
    assert isinstance(created.checked_at, datetime)
    assert created.checked_at.tzinfo is not None


@pytest.mark.asyncio
async def test_persist_updates_existing_record():
    service, repository = build_service()

    customer_id = uuid4()

    existing = CustomerDataQualityRecord(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        status="matched",
        mismatches=[],
        missing=[],
        fields={},
    )

    repository.find_for_identity.return_value = existing

    result = build_result(
        status="mismatch",
        mismatches=["company_name"],
        fields={
            "company_name": {
                "status": "mismatch",
            }
        },
    )

    persisted = await service.persist(
        customer_id=customer_id,
        external_id="12345",
        reconciliation=result,
    )

    assert persisted is existing

    assert existing.status == "mismatch"
    assert existing.mismatches == ["company_name"]
    assert existing.missing == []
    assert existing.fields == {
        "company_name": {
            "status": "mismatch",
            "canonical_value": None,
            "source_value": None,
        }
    }
    assert existing.checked_at.tzinfo is not None

    repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_persist_updates_missing_fields():
    service, repository = build_service()

    customer_id = uuid4()

    existing = CustomerDataQualityRecord(
        customer_id=customer_id,
        source="xero",
        entity_type="contact",
        external_id="contact-123",
        status="matched",
        mismatches=[],
        missing=[],
        fields={},
    )

    repository.find_for_identity.return_value = existing

    result = build_result(
        source="xero",
        entity_type="contact",
        status="incomplete",
        missing=["email"],
        fields={
            "email": {
                "status": "missing_on_source",
            }
        },
    )

    persisted = await service.persist(
        customer_id=customer_id,
        external_id="contact-123",
        reconciliation=result,
    )

    assert persisted is existing
    assert existing.status == "incomplete"
    assert existing.missing == ["email"]
    assert existing.mismatches == []
    assert existing.fields == {
        "email": {
            "status": "missing_on_source",
            "canonical_value": None,
            "source_value": None,
        }
    }


@pytest.mark.asyncio
async def test_persist_requires_timezone_aware_checked_at():
    service, repository = build_service()

    customer_id = uuid4()

    repository.find_for_identity.return_value = None
    repository.create.return_value = MagicMock()

    result = build_result()

    await service.persist(
        customer_id=customer_id,
        external_id="12345",
        reconciliation=result,
    )

    created = repository.create.await_args.args[0]

    assert created.checked_at.tzinfo == timezone.utc


@pytest.mark.asyncio
async def test_persist_serializes_field_reconciliation_objects():
    service, repository = build_service()

    customer_id = uuid4()

    repository.find_for_identity.return_value = None
    repository.create.return_value = MagicMock()

    result = build_result(
        fields={
            "company_name": MagicMock(
                field="company_name",
                status=MagicMock(value="match"),
                canonical_value="acme ai",
                source_value="acme ai",
                ownership=None,
                classification=None,
            ),
        },
    )

    await service.persist(
        customer_id=customer_id,
        external_id="12345",
        reconciliation=result,
    )

    created = repository.create.await_args.args[0]

    assert created.fields == {
        "company_name": {
            "status": "match",
            "canonical_value": "acme ai",
            "source_value": "acme ai",
        }
    }


@pytest.mark.asyncio
async def test_persist_serializes_field_ownership_classification():
    service, repository = build_service()

    customer_id = uuid4()

    repository.find_for_identity.return_value = None
    repository.create.return_value = MagicMock()

    result = build_result(
        status="mismatch",
        fields={},
    )

    field_result = MagicMock()
    field_result.status = MagicMock(value="mismatch")
    field_result.canonical_value = "acme ai"
    field_result.source_value = "acme compute"
    field_result.ownership = MagicMock(value="authoritative")
    field_result.classification = MagicMock(
        value="authoritative_mismatch"
    )

    result.fields = {
        "company_name": field_result,
    }

    await service.persist(
        customer_id=customer_id,
        external_id="12345",
        reconciliation=result,
    )

    created = repository.create.await_args.args[0]

    assert created.fields == {
        "company_name": {
            "status": "mismatch",
            "canonical_value": "acme ai",
            "source_value": "acme compute",
            "ownership": "authoritative",
            "classification": "authoritative_mismatch",
        }
    }
