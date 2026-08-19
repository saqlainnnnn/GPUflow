from apps.gpuaas.app.services.customer_reconciliation import (
    FieldReconciliationStatus,
    compare_customer_fields,
    normalize_customer_fields,
)


def test_matching_fields_are_reported_as_match():
    canonical = normalize_customer_fields(
        company_name="Acme AI",
        email="hello@acme.ai",
        country="IN",
    )

    source = normalize_customer_fields(
        company_name="  ACME   AI ",
        email="HELLO@ACME.AI",
        country="in",
    )

    result = compare_customer_fields(
        canonical=canonical,
        source=source,
    )

    assert result["company_name"].status is FieldReconciliationStatus.MATCH
    assert result["email"].status is FieldReconciliationStatus.MATCH
    assert result["country"].status is FieldReconciliationStatus.MATCH


def test_different_values_are_reported_as_mismatch():
    canonical = normalize_customer_fields(
        company_name="Acme AI",
        email="hello@acme.ai",
        country="IN",
    )

    source = normalize_customer_fields(
        company_name="Acme Compute",
        email="billing@acme.ai",
        country="US",
    )

    result = compare_customer_fields(
        canonical=canonical,
        source=source,
    )

    assert (
        result["company_name"].status
        is FieldReconciliationStatus.MISMATCH
    )
    assert (
        result["email"].status
        is FieldReconciliationStatus.MISMATCH
    )
    assert (
        result["country"].status
        is FieldReconciliationStatus.MISMATCH
    )


def test_missing_source_values_are_reported_separately():
    canonical = normalize_customer_fields(
        company_name="Acme AI",
        email="hello@acme.ai",
        country="IN",
    )

    source = normalize_customer_fields(
        company_name="Acme AI",
        email=None,
        country=None,
    )

    result = compare_customer_fields(
        canonical=canonical,
        source=source,
    )

    assert result["company_name"].status is FieldReconciliationStatus.MATCH

    assert (
        result["email"].status
        is FieldReconciliationStatus.MISSING_ON_SOURCE
    )

    assert (
        result["country"].status
        is FieldReconciliationStatus.MISSING_ON_SOURCE
    )


def test_missing_canonical_values_are_reported_separately():
    canonical = normalize_customer_fields(
        company_name="Acme AI",
        email=None,
        country=None,
    )

    source = normalize_customer_fields(
        company_name="Acme AI",
        email="hello@acme.ai",
        country="IN",
    )

    result = compare_customer_fields(
        canonical=canonical,
        source=source,
    )

    assert result["company_name"].status is FieldReconciliationStatus.MATCH

    assert (
        result["email"].status
        is FieldReconciliationStatus.MISSING_ON_CANONICAL
    )

    assert (
        result["country"].status
        is FieldReconciliationStatus.MISSING_ON_CANONICAL
    )


def test_both_missing_values_are_treated_as_match():
    canonical = normalize_customer_fields(
        company_name="Acme AI",
        email=None,
        country=None,
    )

    source = normalize_customer_fields(
        company_name="Acme AI",
        email=None,
        country=None,
    )

    result = compare_customer_fields(
        canonical=canonical,
        source=source,
    )

    assert result["company_name"].status is FieldReconciliationStatus.MATCH
    assert result["email"].status is FieldReconciliationStatus.MATCH
    assert result["country"].status is FieldReconciliationStatus.MATCH
