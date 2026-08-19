from apps.gpuaas.app.services.customer_field_ownership import (
    CustomerFieldOwnershipPolicy,
)
from apps.gpuaas.app.services.customer_field_ownership_provider import (
    CustomerFieldOwnershipProvider,
)


def test_default_provider_returns_customer_policy():
    provider = CustomerFieldOwnershipProvider()

    policy = provider.for_customer()

    assert isinstance(
        policy,
        CustomerFieldOwnershipPolicy,
    )


def test_default_customer_policy_uses_pipedrive_as_authority():
    provider = CustomerFieldOwnershipProvider()

    policy = provider.for_customer()

    assert (
        policy.authoritative_source(
            field="company_name"
        )
        == "pipedrive"
    )

    assert (
        policy.authoritative_source(
            field="email"
        )
        == "pipedrive"
    )

    assert (
        policy.authoritative_source(
            field="country"
        )
        == "pipedrive"
    )


def test_provider_returns_independent_policy_instances():
    provider = CustomerFieldOwnershipProvider()

    first = provider.for_customer()
    second = provider.for_customer()

    assert first is not second
