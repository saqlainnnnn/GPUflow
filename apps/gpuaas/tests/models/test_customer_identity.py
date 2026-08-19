from uuid import uuid4

from sqlalchemy import UniqueConstraint, inspect

from apps.gpuaas.app.models.customer import Customer
from apps.gpuaas.app.models.customer_identity import CustomerIdentity


def test_customer_identity_has_expected_fields():
    columns = inspect(CustomerIdentity).columns

    assert "id" in columns
    assert "customer_id" in columns
    assert "source" in columns
    assert "entity_type" in columns
    assert "external_id" in columns
    assert "created_at" in columns
    assert "updated_at" in columns


def test_customer_identity_links_to_customer():
    identity = CustomerIdentity(
        customer_id=uuid4(),
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
    )

    assert identity.customer_id is not None
    assert identity.source == "pipedrive"
    assert identity.entity_type == "organization"
    assert identity.external_id == "12345"


def test_customer_identity_has_unique_external_identity_constraint():
    constraints = CustomerIdentity.__table__.constraints

    assert any(
        isinstance(constraint, UniqueConstraint)
        and {column.name for column in constraint.columns}
        == {"source", "entity_type", "external_id"}
        for constraint in constraints
    )


def test_customer_identity_has_unique_customer_source_constraint():
    constraints = CustomerIdentity.__table__.constraints

    assert any(
        isinstance(constraint, UniqueConstraint)
        and {column.name for column in constraint.columns}
        == {"customer_id", "source", "entity_type"}
        for constraint in constraints
    )


def test_customer_has_identities_relationship():
    assert hasattr(Customer, "identities")
