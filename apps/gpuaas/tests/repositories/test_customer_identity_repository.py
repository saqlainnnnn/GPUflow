from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.models.customer_identity import CustomerIdentity
from apps.gpuaas.app.repositories.customer_identity import (
    CustomerIdentityRepository,
)


def build_repository():
    session = AsyncMock()
    session.add = MagicMock()

    repository = CustomerIdentityRepository(session)

    return repository, session


@pytest.mark.asyncio
async def test_find_by_external_identity_returns_identity():
    repository, session = build_repository()

    customer_id = uuid4()
    identity = CustomerIdentity(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    result_proxy = MagicMock()
    result_proxy.scalar_one_or_none.return_value = identity
    session.execute.return_value = result_proxy

    result = await repository.find_by_external_identity(
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    assert result is identity
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_find_by_external_identity_returns_none_when_missing():
    repository, session = build_repository()

    result_proxy = MagicMock()
    result_proxy.scalar_one_or_none.return_value = None
    session.execute.return_value = result_proxy

    result = await repository.find_by_external_identity(
        source="pipedrive",
        entity_type="organization",
        external_id="does-not-exist",
    )

    assert result is None
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_find_for_customer_returns_identities():
    repository, session = build_repository()

    customer_id = uuid4()

    identity = CustomerIdentity(
        customer_id=customer_id,
        source="xero",
        entity_type="contact",
        external_id="xero-123",
    )

    result_proxy = MagicMock()
    result_proxy.scalars.return_value.all.return_value = [identity]
    session.execute.return_value = result_proxy

    result = await repository.find_for_customer(customer_id)

    assert result == [identity]
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_persists_identity():
    repository, session = build_repository()

    identity = CustomerIdentity(
        customer_id=uuid4(),
        source="xero",
        entity_type="contact",
        external_id="xero-123",
    )

    result = await repository.create(identity)

    assert result is identity
    session.add.assert_called_once_with(identity)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(identity)
