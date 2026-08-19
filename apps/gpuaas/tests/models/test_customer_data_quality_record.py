from uuid import uuid4

from sqlalchemy import UniqueConstraint, inspect

from apps.gpuaas.app.models.customer_data_quality import (
    CustomerDataQualityRecord,
)


def test_customer_data_quality_record_has_expected_fields():
    columns = inspect(CustomerDataQualityRecord).columns

    assert "id" in columns
    assert "customer_id" in columns
    assert "source" in columns
    assert "entity_type" in columns
    assert "external_id" in columns
    assert "status" in columns
    assert "mismatches" in columns
    assert "missing" in columns
    assert "fields" in columns
    assert "checked_at" in columns


def test_customer_data_quality_record_can_be_constructed():
    record = CustomerDataQualityRecord(
        customer_id=uuid4(),
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        status="matched",
        mismatches=[],
        missing=[],
        fields={},
    )

    assert record.customer_id is not None
    assert record.source == "pipedrive"
    assert record.entity_type == "organization"
    assert record.external_id == "12345"
    assert record.status == "matched"
    assert record.mismatches == []
    assert record.missing == []
    assert record.fields == {}


def test_customer_data_quality_record_has_unique_source_identity():
    constraints = CustomerDataQualityRecord.__table__.constraints

    assert any(
        isinstance(constraint, UniqueConstraint)
        and {
            column.name
            for column in constraint.columns
        }
        == {
            "customer_id",
            "source",
            "entity_type",
            "external_id",
        }
        for constraint in constraints
    )
