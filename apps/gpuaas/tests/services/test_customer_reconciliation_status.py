from apps.gpuaas.app.services.customer_reconciliation import (
    FieldReconciliation,
    FieldReconciliationStatus,
    CustomerReconciliationStatus,
    summarize_customer_reconciliation,
)


def field(name, status, canonical="canonical", source="source"):
    return FieldReconciliation(
        field=name,
        status=status,
        canonical_value=canonical,
        source_value=source,
    )


def test_all_matching_fields_produce_matched_status():
    result = summarize_customer_reconciliation(
        {
            "company_name": field(
                "company_name",
                FieldReconciliationStatus.MATCH,
            ),
            "email": field(
                "email",
                FieldReconciliationStatus.MATCH,
            ),
            "country": field(
                "country",
                FieldReconciliationStatus.MATCH,
            ),
        }
    )

    assert result.status is CustomerReconciliationStatus.MATCHED
    assert result.mismatches == []
    assert result.missing == []


def test_missing_source_fields_produce_incomplete_status():
    result = summarize_customer_reconciliation(
        {
            "company_name": field(
                "company_name",
                FieldReconciliationStatus.MATCH,
            ),
            "email": field(
                "email",
                FieldReconciliationStatus.MISSING_ON_SOURCE,
            ),
            "country": field(
                "country",
                FieldReconciliationStatus.MATCH,
            ),
        }
    )

    assert result.status is CustomerReconciliationStatus.INCOMPLETE
    assert result.mismatches == []
    assert result.missing == ["email"]


def test_missing_canonical_fields_produce_incomplete_status():
    result = summarize_customer_reconciliation(
        {
            "company_name": field(
                "company_name",
                FieldReconciliationStatus.MATCH,
            ),
            "email": field(
                "email",
                FieldReconciliationStatus.MISSING_ON_CANONICAL,
            ),
            "country": field(
                "country",
                FieldReconciliationStatus.MATCH,
            ),
        }
    )

    assert result.status is CustomerReconciliationStatus.INCOMPLETE
    assert result.mismatches == []
    assert result.missing == ["email"]


def test_any_mismatch_produces_mismatch_status():
    result = summarize_customer_reconciliation(
        {
            "company_name": field(
                "company_name",
                FieldReconciliationStatus.MATCH,
            ),
            "email": field(
                "email",
                FieldReconciliationStatus.MISMATCH,
            ),
            "country": field(
                "country",
                FieldReconciliationStatus.MATCH,
            ),
        }
    )

    assert result.status is CustomerReconciliationStatus.MISMATCH
    assert result.mismatches == ["email"]
    assert result.missing == []


def test_mismatch_takes_precedence_over_missing_data():
    result = summarize_customer_reconciliation(
        {
            "company_name": field(
                "company_name",
                FieldReconciliationStatus.MISMATCH,
            ),
            "email": field(
                "email",
                FieldReconciliationStatus.MISSING_ON_SOURCE,
            ),
            "country": field(
                "country",
                FieldReconciliationStatus.MATCH,
            ),
        }
    )

    assert result.status is CustomerReconciliationStatus.MISMATCH
    assert result.mismatches == ["company_name"]
    assert result.missing == ["email"]


def test_empty_field_set_is_matched():
    result = summarize_customer_reconciliation({})

    assert result.status is CustomerReconciliationStatus.MATCHED
    assert result.mismatches == []
    assert result.missing == []
