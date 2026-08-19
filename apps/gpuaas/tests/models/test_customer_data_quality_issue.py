from uuid import uuid4

from sqlalchemy import UniqueConstraint, inspect

from apps.gpuaas.app.models.customer_data_quality_issue import (
    CustomerDataQualityIssue,
)


def test_issue_has_expected_fields():
    columns = inspect(CustomerDataQualityIssue).columns

    assert "id" in columns
    assert "customer_id" in columns
    assert "issue_type" in columns
    assert "source" in columns
    assert "entity_type" in columns
    assert "external_id" in columns
    assert "status" in columns
    assert "details" in columns
    assert "detected_at" in columns
    assert "resolved_at" in columns


def test_issue_can_represent_orphan_without_customer():
    issue = CustomerDataQualityIssue(
        customer_id=None,
        issue_type="orphaned_source",
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        status="open",
        details={
            "reason": "no_customer_identity",
        },
    )

    assert issue.customer_id is None
    assert issue.issue_type == "orphaned_source"
    assert issue.status == "open"
    assert issue.details["reason"] == "no_customer_identity"


def test_issue_has_unique_identity_constraint():
    constraints = CustomerDataQualityIssue.__table__.constraints

    assert any(
        isinstance(constraint, UniqueConstraint)
        and {
            column.name
            for column in constraint.columns
        }
        == {
            "issue_type",
            "source",
            "entity_type",
            "external_id",
        }
        for constraint in constraints
    )
