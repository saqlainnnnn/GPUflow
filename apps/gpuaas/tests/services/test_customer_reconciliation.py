from uuid import uuid4

import pytest

from apps.gpuaas.app.services.customer_reconciliation import (
    normalize_customer_fields,
)


def test_normalize_company_name():
    result = normalize_customer_fields(
        company_name="  Acme   AI  ",
        email="HELLO@ACME.AI",
        country="in",
    )

    assert result.company_name == "acme ai"
    assert result.email == "hello@acme.ai"
    assert result.country == "IN"


def test_normalize_empty_company_name():
    result = normalize_customer_fields(
        company_name=None,
        email="HELLO@ACME.AI",
        country="in",
    )

    assert result.company_name is None
    assert result.email == "hello@acme.ai"
    assert result.country == "IN"


def test_normalize_empty_email():
    result = normalize_customer_fields(
        company_name="Acme AI",
        email=None,
        country="IN",
    )

    assert result.company_name == "acme ai"
    assert result.email is None
    assert result.country == "IN"


@pytest.mark.parametrize(
    ("country", "expected"),
    [
        ("in", "IN"),
        (" IN ", "IN"),
        ("us", "US"),
        ("Us", "US"),
        (None, None),
    ],
)
def test_normalize_country(country, expected):
    result = normalize_customer_fields(
        company_name="Acme AI",
        email="hello@acme.ai",
        country=country,
    )

    assert result.country == expected
