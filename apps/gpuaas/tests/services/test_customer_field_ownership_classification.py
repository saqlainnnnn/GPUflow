from apps.gpuaas.app.services.customer_field_ownership import (
    CustomerFieldOwnershipPolicy,
    OwnershipDecision,
)
from apps.gpuaas.app.services.customer_field_ownership_classification import (
    FieldOwnershipClassification,
    classify_reconciliation_fields,
)
from apps.gpuaas.app.services.customer_reconciliation import (
    FieldReconciliation,
    FieldReconciliationStatus,
)


def build_policy():
    return CustomerFieldOwnershipPolicy(
        {
            "company_name": "pipedrive",
            "email": "pipedrive",
            "country": "pipedrive",
        }
    )


def field(
    name,
    status,
    canonical="canonical",
    source="source",
):
    return FieldReconciliation(
        field=name,
        status=status,
        canonical_value=canonical,
        source_value=source,
    )


def test_authoritative_mismatch_is_classified():
    policy = build_policy()

    result = classify_reconciliation_fields(
        fields={
            "email": field(
                "email",
                FieldReconciliationStatus.MISMATCH,
            )
        },
        source="pipedrive",
        policy=policy,
    )

    assert (
        result["email"].classification
        is FieldOwnershipClassification.AUTHORITATIVE_MISMATCH
    )

    assert (
        result["email"].ownership
        is OwnershipDecision.AUTHORITATIVE
    )


def test_non_authoritative_mismatch_is_classified():
    policy = build_policy()

    result = classify_reconciliation_fields(
        fields={
            "email": field(
                "email",
                FieldReconciliationStatus.MISMATCH,
            )
        },
        source="xero",
        policy=policy,
    )

    assert (
        result["email"].classification
        is FieldOwnershipClassification.NON_AUTHORITATIVE_MISMATCH
    )

    assert (
        result["email"].ownership
        is OwnershipDecision.NON_AUTHORITATIVE
    )


def test_missing_authoritative_field_is_classified():
    policy = build_policy()

    result = classify_reconciliation_fields(
        fields={
            "email": field(
                "email",
                FieldReconciliationStatus.MISSING_ON_SOURCE,
            )
        },
        source="pipedrive",
        policy=policy,
    )

    assert (
        result["email"].classification
        is FieldOwnershipClassification.MISSING_AUTHORITATIVE
    )


def test_missing_non_authoritative_field_is_classified():
    policy = build_policy()

    result = classify_reconciliation_fields(
        fields={
            "email": field(
                "email",
                FieldReconciliationStatus.MISSING_ON_SOURCE,
            )
        },
        source="xero",
        policy=policy,
    )

    assert (
        result["email"].classification
        is FieldOwnershipClassification.MISSING_NON_AUTHORITATIVE
    )


def test_match_is_not_an_issue():
    policy = build_policy()

    result = classify_reconciliation_fields(
        fields={
            "email": field(
                "email",
                FieldReconciliationStatus.MATCH,
            )
        },
        source="xero",
        policy=policy,
    )

    assert result["email"].classification is None


def test_classification_preserves_field_values():
    policy = build_policy()

    result = classify_reconciliation_fields(
        fields={
            "email": field(
                "email",
                FieldReconciliationStatus.MISMATCH,
                canonical="a@acme.ai",
                source="b@acme.ai",
            )
        },
        source="pipedrive",
        policy=policy,
    )

    assert result["email"].canonical_value == "a@acme.ai"
    assert result["email"].source_value == "b@acme.ai"
