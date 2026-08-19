import pytest

from apps.gpuaas.app.services.customer_field_ownership import (
    CustomerFieldOwnershipPolicy,
    OwnershipDecision,
)


def build_policy():
    return CustomerFieldOwnershipPolicy(
        {
            "company_name": "pipedrive",
            "email": "pipedrive",
            "country": "pipedrive",
        }
    )


def test_authoritative_source_is_returned():
    policy = build_policy()

    result = policy.authoritative_source(
        field="company_name",
    )

    assert result == "pipedrive"


def test_non_authoritative_source_is_not_owner():
    policy = build_policy()

    result = policy.decide(
        field="email",
        source="xero",
    )

    assert result is OwnershipDecision.NON_AUTHORITATIVE


def test_authoritative_source_is_owner():
    policy = build_policy()

    result = policy.decide(
        field="email",
        source="pipedrive",
    )

    assert result is OwnershipDecision.AUTHORITATIVE


def test_unknown_field_returns_unknown():
    policy = build_policy()

    result = policy.decide(
        field="some_new_field",
        source="pipedrive",
    )

    assert result is OwnershipDecision.UNKNOWN


def test_unknown_source_is_non_authoritative():
    policy = build_policy()

    result = policy.decide(
        field="email",
        source="unknown_source",
    )

    assert result is OwnershipDecision.NON_AUTHORITATIVE


@pytest.mark.parametrize(
    ("field", "source"),
    [
        ("company_name", "pipedrive"),
        ("email", "pipedrive"),
        ("country", "pipedrive"),
    ],
)
def test_default_policy_contains_expected_ownership(
    field,
    source,
):
    policy = build_policy()

    assert (
        policy.decide(
            field=field,
            source=source,
        )
        is OwnershipDecision.AUTHORITATIVE
    )
