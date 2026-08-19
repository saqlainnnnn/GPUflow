from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.models.kyb_audit import KYBAudit
from apps.gpuaas.app.repositories.kyb_audit import (
    KYBAuditRepository,
)


@pytest.mark.asyncio
async def test_create_persists_kyb_audit():
    session = AsyncMock()
    session.add = MagicMock()

    repository = KYBAuditRepository(session)

    audit = KYBAudit(
        customer_id=uuid4(),
        check_type="restricted_country",
        input_snapshot={
            "company_name": "Acme AI",
            "country": "XX",
        },
        decision="blocked",
        reason="Restricted country",
        reviewer=None,
    )

    result = await repository.create(audit)

    assert result is audit
    session.add.assert_called_once_with(audit)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(audit)
