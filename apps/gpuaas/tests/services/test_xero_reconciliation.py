from apps.gpuaas.app.services.xero_reconciliation import (
    XeroContactReconciliationAdapter,
)


def test_adapts_xero_contact():
    adapter = XeroContactReconciliationAdapter()

    result = adapter.to_customer_record(
        {
            "ContactID": "contact-123",
            "Name": "  Acme   AI ",
            "EmailAddress": "HELLO@ACME.AI",
            "Country": "in",
        }
    )

    assert result == {
        "company_name": "  Acme   AI ",
        "email": "HELLO@ACME.AI",
        "country": "in",
    }


def test_preserves_missing_values():
    adapter = XeroContactReconciliationAdapter()

    result = adapter.to_customer_record(
        {
            "ContactID": "contact-123",
            "Name": "Acme AI",
        }
    )

    assert result == {
        "company_name": "Acme AI",
        "email": None,
        "country": None,
    }


def test_ignores_unrelated_xero_fields():
    adapter = XeroContactReconciliationAdapter()

    result = adapter.to_customer_record(
        {
            "ContactID": "contact-123",
            "Name": "Acme AI",
            "EmailAddress": "hello@acme.ai",
            "Country": "IN",
            "IsCustomer": True,
            "ContactNumber": "ABC-123",
            "Addresses": [],
        }
    )

    assert result == {
        "company_name": "Acme AI",
        "email": "hello@acme.ai",
        "country": "IN",
    }


def test_empty_contact_is_supported():
    adapter = XeroContactReconciliationAdapter()

    result = adapter.to_customer_record({})

    assert result == {
        "company_name": None,
        "email": None,
        "country": None,
    }
