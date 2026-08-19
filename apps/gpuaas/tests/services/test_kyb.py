from uuid import uuid4

import pytest

from apps.gpuaas.app.services.kyb import (
    DENIED_PARTIES,
    RESTRICTED_COUNTRIES,
    KYBDecision,
    KYBScreeningService,
)


def build_service():
    return KYBScreeningService()


def test_clear_customer():
    service = build_service()

    result = service.screen_customer(
        company_name="Acme AI",
        country="IN",
    )

    assert result.decision == KYBDecision.CLEAR
    assert result.checks == []


def test_restricted_country_is_blocked():
    service = build_service()

    country = next(iter(RESTRICTED_COUNTRIES))

    result = service.screen_customer(
        company_name="Acme AI",
        country=country,
    )

    assert result.decision == KYBDecision.BLOCKED
    assert len(result.checks) == 1
    assert result.checks[0].check_type == (
        "restricted_country"
    )


def test_denied_party_exact_match_is_blocked():
    service = build_service()

    company_name = next(iter(DENIED_PARTIES))

    result = service.screen_customer(
        company_name=company_name,
        country="IN",
    )

    assert result.decision == KYBDecision.FLAGGED
    assert len(result.checks) == 1
    assert result.checks[0].check_type == (
        "denied_party"
    )


def test_denied_party_normalization_is_flagged():
    service = build_service()

    company_name = next(iter(DENIED_PARTIES))

    result = service.screen_customer(
        company_name=f"  {company_name.upper()}  ",
        country="IN",
    )

    assert result.decision == KYBDecision.FLAGGED
    assert result.checks[0].check_type == (
        "denied_party"
    )


def test_denied_party_fuzzy_match_is_flagged():
    service = build_service()

    company_name = next(iter(DENIED_PARTIES))

    result = service.screen_customer(
        company_name=company_name.replace(
            "Ltd",
            "Limited",
        ),
        country="IN",
    )

    assert result.decision == KYBDecision.FLAGGED
    assert result.checks[0].check_type == (
        "denied_party"
    )


def test_near_miss_is_clear():
    service = build_service()

    company_name = next(iter(DENIED_PARTIES))

    result = service.screen_customer(
        company_name=f"{company_name} Technologies",
        country="IN",
    )

    assert result.decision == KYBDecision.CLEAR


def test_multiple_checks_are_returned():
    service = build_service()

    country = next(iter(RESTRICTED_COUNTRIES))
    company_name = next(iter(DENIED_PARTIES))

    result = service.screen_customer(
        company_name=company_name,
        country=country,
    )

    assert result.decision == KYBDecision.BLOCKED

    check_types = {
        check.check_type
        for check in result.checks
    }

    assert check_types == {
        "restricted_country",
        "denied_party",
    }


@pytest.mark.parametrize(
    "country",
    [
        "in",
        " IN ",
        "In",
    ],
)
def test_country_is_normalized(country):
    service = build_service()

    result = service.screen_customer(
        company_name="Acme AI",
        country=country,
    )

    assert result.decision == KYBDecision.CLEAR
