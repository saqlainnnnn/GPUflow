from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.services.kyb import (
    KYBCheck,
    KYBDecision,
    KYBScreeningResult,
)
from apps.gpuaas.app.services.kyb_audit import (
    KYBAuditService,
)


def build_service():
    repository = AsyncMock()

    return (
        KYBAuditService(
            repository=repository,
        ),
        repository,
    )


@pytest.mark.asyncio
async def test_persist_blocked_decision():
    service, repository = build_service()

    customer_id = uuid4()

    result = KYBScreeningResult(
        decision=KYBDecision.BLOCKED,
        checks=[
            KYBCheck(
                check_type="restricted_country",
                reason="Restricted country",
                matched_value="XX",
            ),
        ],
    )

    await service.record_screening(
        customer_id=customer_id,
        company_name="Acme AI",
        country="XX",
        result=result,
    )

    repository.create.assert_awaited_once()

    audit = repository.create.await_args.args[0]

    assert audit.customer_id == customer_id
    assert audit.check_type == "restricted_country"
    assert audit.decision == "blocked"
    assert audit.reason == "Restricted country"
    assert audit.input_snapshot == {
        "company_name": "Acme AI",
        "country": "XX",
    }
    assert audit.reviewer is None


@pytest.mark.asyncio
async def test_persist_clear_decision():
    service, repository = build_service()

    customer_id = uuid4()

    result = KYBScreeningResult(
        decision=KYBDecision.CLEAR,
        checks=[],
    )

    await service.record_screening(
        customer_id=customer_id,
        company_name="Acme AI",
        country="IN",
        result=result,
    )

    repository.create.assert_awaited_once()

    audit = repository.create.await_args.args[0]

    assert audit.customer_id == customer_id
    assert audit.check_type == "screening"
    assert audit.decision == "clear"
    assert audit.reason == "No screening violations detected."
    assert audit.input_snapshot == {
        "company_name": "Acme AI",
        "country": "IN",
    }


@pytest.mark.asyncio
async def test_persist_multiple_triggered_checks():
    service, repository = build_service()

    customer_id = uuid4()

    result = KYBScreeningResult(
        decision=KYBDecision.BLOCKED,
        checks=[
            KYBCheck(
                check_type="restricted_country",
                reason="Restricted country",
                matched_value="XX",
            ),
            KYBCheck(
                check_type="denied_party",
                reason="Denied party match",
                matched_value="Blocked Compute Ltd",
            ),
        ],
    )

    repository.create.side_effect = (
        lambda audit: audit
    )

    await service.record_screening(
        customer_id=customer_id,
        company_name="Blocked Compute Ltd",
        country="XX",
        result=result,
    )

    assert repository.create.await_count == 2

    first = repository.create.await_args_list[0].args[0]
    second = repository.create.await_args_list[1].args[0]

    assert first.check_type == "restricted_country"
    assert second.check_type == "denied_party"
