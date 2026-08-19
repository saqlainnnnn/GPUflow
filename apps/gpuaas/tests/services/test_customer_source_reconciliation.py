from uuid import uuid4

import pytest

from apps.gpuaas.app.models.customer import Customer
from apps.gpuaas.app.services.customer_reconciliation import (
    CustomerReconciliationStatus,
    reconcile_customer_source,
)


def build_customer(
    *,
    company_name="Acme AI",
    email="hello@acme.ai",
    country="IN",
):
    return Customer(
        id=uuid4(),
        external_id=f"customer-{uuid4()}",
        company_name=company_name,
        email=email,
        country=country,
        status="active",
    )


def test_matching_source_produces_matched_reconciliation():
    customer = build_customer()

    result = reconcile_customer_source(
        customer=customer,
        source="pipedrive",
        entity_type="organization",
        source_record={
            "company_name": "  ACME AI ",
            "email": "HELLO@ACME.AI",
            "country": "in",
        },
    )

    assert result.source == "pipedrive"
    assert result.entity_type == "organization"
    assert result.status is CustomerReconciliationStatus.MATCHED
    assert result.mismatches == []
    assert result.missing == []


def test_source_mismatch_is_reported():
    customer = build_customer()

    result = reconcile_customer_source(
        customer=customer,
        source="pipedrive",
        entity_type="organization",
        source_record={
            "company_name": "Acme Compute",
            "email": "hello@acme.ai",
            "country": "IN",
        },
    )

    assert result.status is CustomerReconciliationStatus.MISMATCH
    assert result.mismatches == ["company_name"]
    assert result.missing == []


def test_missing_source_fields_are_reported():
    customer = build_customer()

    result = reconcile_customer_source(
        customer=customer,
        source="xero",
        entity_type="contact",
        source_record={
            "company_name": "Acme AI",
            "email": None,
            "country": None,
        },
    )

    assert result.status is CustomerReconciliationStatus.INCOMPLETE
    assert result.mismatches == []
    assert result.missing == ["email", "country"]


def test_source_record_with_extra_fields_is_ignored():
    customer = build_customer()

    result = reconcile_customer_source(
        customer=customer,
        source="xero",
        entity_type="contact",
        source_record={
            "company_name": "Acme AI",
            "email": "hello@acme.ai",
            "country": "IN",
            "ContactID": "xero-123",
            "Name": "Acme AI",
            "IsCustomer": True,
        },
    )

    assert result.status is CustomerReconciliationStatus.MATCHED


def test_customer_missing_canonical_field_is_reported():
    customer = build_customer(
        email=None,
    )

    result = reconcile_customer_source(
        customer=customer,
        source="pipedrive",
        entity_type="organization",
        source_record={
            "company_name": "Acme AI",
            "email": "hello@acme.ai",
            "country": "IN",
        },
    )

    assert result.status is CustomerReconciliationStatus.INCOMPLETE
    assert result.missing == ["email"]
