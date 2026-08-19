from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.models.customer_data_quality import (
    CustomerDataQualityRecord,
)
from apps.gpuaas.app.repositories.customer_data_quality import (
    CustomerDataQualityRepository,
)


def build_repository():
    session = AsyncMock()
    session.add = MagicMock()

    return (
        CustomerDataQualityRepository(session),
        session,
    )


@pytest.mark.asyncio
async def test_find_for_identity_returns_record():
    repository, session = build_repository()

    record = CustomerDataQualityRecord(
        customer_id=uuid4(),
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        status="matched",
        mismatches=[],
        missing=[],
        fields={},
    )

    result_proxy = MagicMock()
    result_proxy.scalar_one_or_none.return_value = record
    session.execute.return_value = result_proxy

    result = await repository.find_for_identity(
        customer_id=record.customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    assert result is record
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_find_for_identity_returns_none_when_missing():
    repository, session = build_repository()

    result_proxy = MagicMock()
    result_proxy.scalar_one_or_none.return_value = None
    session.execute.return_value = result_proxy

    result = await repository.find_for_identity(
        customer_id=uuid4(),
        source="pipedrive",
        entity_type="organization",
        external_id="missing",
    )

    assert result is None
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_find_for_customer_returns_records():
    repository, session = build_repository()

    customer_id = uuid4()

    record = CustomerDataQualityRecord(
        customer_id=customer_id,
        source="xero",
        entity_type="contact",
        external_id="456",
        status="incomplete",
        mismatches=[],
        missing=["email"],
        fields={},
    )

    result_proxy = MagicMock()
    result_proxy.scalars.return_value.all.return_value = [record]
    session.execute.return_value = result_proxy

    result = await repository.find_for_customer(
        customer_id
    )

    assert result == [record]
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_persists_record():
    repository, session = build_repository()

    record = CustomerDataQualityRecord(
        customer_id=uuid4(),
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        status="matched",
        mismatches=[],
        missing=[],
        fields={},
    )

    result = await repository.create(record)

    assert result is record
    session.add.assert_called_once_with(record)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(record)
