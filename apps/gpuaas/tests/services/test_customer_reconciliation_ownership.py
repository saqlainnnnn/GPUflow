from uuid import uuid4

import pytest

from apps.gpuaas.app.services.customer_field_ownership import (
    CustomerFieldOwnershipPolicy,
    OwnershipDecision,
)
from apps.gpuaas.app.services.customer_field_ownership_classification import (
    FieldOwnershipClassification,
)
from apps.gpuaas.app.services.customer_reconciliation import (
    FieldReconciliationStatus,
    reconcile_customer_source,
)
from apps.gpuaas.app.models.customer import Customer


def build_customer():
    return Customer(
        id=uuid4(),
        external_id=f"customer-{uuid4()}",
        company_name="Acme AI",
        email="hello@acme.ai",
        country="IN",
        status="active",
    )


def build_policy():
    return CustomerFieldOwnershipPolicy(
        {
            "company_name": "pipedrive",
            "email": "pipedrive",
            "country": "pipedrive",
        }
    )


def test_reconciliation_result_can_be_classified_by_ownership():
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

    policy = build_policy()

    classified = result.classify_ownership(
        policy=policy,
    )

    assert (
        classified["company_name"].classification
        is FieldOwnershipClassification.AUTHORITATIVE_MISMATCH
    )

    assert (
        classified["company_name"].ownership
        is OwnershipDecision.AUTHORITATIVE
    )

    assert (
        classified["email"].classification is None
    )


def test_xero_mismatch_is_non_authoritative():
    customer = build_customer()

    result = reconcile_customer_source(
        customer=customer,
        source="xero",
        entity_type="contact",
        source_record={
            "company_name": "Acme Compute",
            "email": "hello@acme.ai",
            "country": "IN",
        },
    )

    classified = result.classify_ownership(
        policy=build_policy(),
    )

    assert (
        classified["company_name"].classification
        is FieldOwnershipClassification.NON_AUTHORITATIVE_MISMATCH
    )


@pytest.mark.parametrize(
    "source",
    ["pipedrive", "xero"],
)
def test_match_fields_have_no_ownership_issue(
    source,
):
    customer = build_customer()

    result = reconcile_customer_source(
        customer=customer,
        source=source,
        entity_type=(
            "organization"
            if source == "pipedrive"
            else "contact"
        ),
        source_record={
            "company_name": "Acme AI",
            "email": "hello@acme.ai",
            "country": "IN",
        },
    )

    classified = result.classify_ownership(
        policy=build_policy(),
    )

    for field in classified.values():
        assert field.classification is None
        assert field.status is FieldReconciliationStatus.MATCH
