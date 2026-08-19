from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.models.customer_data_quality_audit import (
    CustomerDataQualityAudit,
)
from apps.gpuaas.app.repositories.customer_data_quality_audit import (
    CustomerDataQualityAuditRepository,
)


@pytest.mark.asyncio
async def test_create_persists_audit():
    session = AsyncMock()
    session.add = MagicMock()

    repository = CustomerDataQualityAuditRepository(
        session
    )

    audit = CustomerDataQualityAudit(
        customer_id=uuid4(),
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        field="company_name",
        decision="source_wins",
        ownership="authoritative",
        canonical_value="Acme AI",
        source_value="Acme Compute",
        resolved_value="Acme Compute",
        resolved_at=__import__(
            "datetime"
        ).datetime.now(
            __import__("datetime").timezone.utc
        ),
    )

    result = await repository.create(audit)

    assert result is audit
    session.add.assert_called_once_with(audit)
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(audit)
