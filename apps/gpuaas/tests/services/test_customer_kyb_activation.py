from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.gpuaas.app.schemas.customer import CustomerCreate
from apps.gpuaas.app.services.customer import CustomerService
from apps.gpuaas.app.services.kyb import (
    KYBCheck,
    KYBDecision,
    KYBScreeningResult,
)


def build_service():
    session = AsyncMock()

    service = CustomerService(session)

    repository = AsyncMock()
    repository.get_by_external_id.return_value = None

    customer = MagicMock()
    repository.create.return_value = customer

    service.repository = repository

    kyb = MagicMock()
    service.kyb = kyb

    return service, session, repository, kyb, customer


def build_data(
    *,
    company_name="Acme AI",
    country="IN",
):
    return CustomerCreate(
        external_id="customer-123",
        company_name=company_name,
        email="hello@acme.ai",
        country=country,
    )


@pytest.mark.asyncio
async def test_clear_customer_becomes_active():
    service, session, repository, kyb, customer = (
        build_service()
    )

    kyb.screen_customer.return_value = (
        KYBScreeningResult(
            decision=KYBDecision.CLEAR,
            checks=[],
        )
    )

    result = await service.create_customer(
        build_data()
    )

    created = repository.create.await_args.args[0]

    assert created.status == "active"
    assert result is customer

    kyb.screen_customer.assert_called_once_with(
        company_name="Acme AI",
        country="IN",
    )


@pytest.mark.asyncio
async def test_flagged_customer_becomes_pending_review():
    service, session, repository, kyb, customer = (
        build_service()
    )

    kyb.screen_customer.return_value = (
        KYBScreeningResult(
            decision=KYBDecision.FLAGGED,
            checks=[
                KYBCheck(
                    check_type="denied_party",
                    reason="Possible match",
                    matched_value=(
                        "Example Restricted Corp"
                    ),
                )
            ],
        )
    )

    result = await service.create_customer(
        build_data(
            company_name="Example Restricted Corp",
        )
    )

    created = repository.create.await_args.args[0]

    assert created.status == "pending_review"
    assert result is customer


@pytest.mark.asyncio
async def test_blocked_customer_becomes_blocked():
    service, session, repository, kyb, customer = (
        build_service()
    )

    kyb.screen_customer.return_value = (
        KYBScreeningResult(
            decision=KYBDecision.BLOCKED,
            checks=[
                KYBCheck(
                    check_type="restricted_country",
                    reason="Restricted country",
                    matched_value="XX",
                )
            ],
        )
    )

    result = await service.create_customer(
        build_data(country="XX")
    )

    created = repository.create.await_args.args[0]

    assert created.status == "blocked"
    assert result is customer


@pytest.mark.asyncio
async def test_customer_creation_records_clear_kyb_audit():
    service, session, repository, kyb, customer = (
        build_service()
    )

    audit_service = AsyncMock()
    service.kyb_audit = audit_service

    kyb.screen_customer.return_value = (
        KYBScreeningResult(
            decision=KYBDecision.CLEAR,
            checks=[],
        )
    )

    await service.create_customer(
        build_data()
    )

    audit_service.record_screening.assert_awaited_once()


@pytest.mark.asyncio
async def test_customer_creation_records_flagged_kyb_audit():
    service, session, repository, kyb, customer = (
        build_service()
    )

    audit_service = AsyncMock()
    service.kyb_audit = audit_service

    result = KYBScreeningResult(
        decision=KYBDecision.FLAGGED,
        checks=[
            KYBCheck(
                check_type="denied_party",
                reason="Possible match",
                matched_value="Example Restricted Corp",
            )
        ],
    )

    kyb.screen_customer.return_value = result

    await service.create_customer(
        build_data(
            company_name="Example Restricted Corp",
        )
    )

    audit_service.record_screening.assert_awaited_once_with(
        customer_id=customer.id,
        company_name="Example Restricted Corp",
        country="IN",
        result=result,
    )
