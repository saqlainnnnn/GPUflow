from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from apps.gpuaas.app.services.xero_invoice import (
    XeroInvoiceCurrencyError,
    XeroInvoiceService,
)


@pytest.fixture
def invoice():
    customer_id = uuid4()

    line_item = SimpleNamespace(
        description="H100 GPU usage",
        gpu_hours=Decimal("10.00"),
        rate_per_gpu_hour=Decimal("2.50"),
    )

    return SimpleNamespace(
        id=uuid4(),
        customer_id=customer_id,
        invoice_number="INV-2026-001",
        period_end=date(2026, 8, 15),
        currency="INR",
        xero_invoice_id=None,
        line_items=[line_item],
    )


@pytest.fixture
def customer():
    return SimpleNamespace(
        id=uuid4(),
        name="Acme AI",
    )


@pytest.fixture
def connection():
    return SimpleNamespace(
        access_token="access-token",
        tenant_id="tenant-id",
    )


def build_service():
    session = AsyncMock()

    service = XeroInvoiceService.__new__(
        XeroInvoiceService,
    )

    service.session = session
    service.invoices = AsyncMock()
    service.customers = AsyncMock()
    service.contacts = AsyncMock()

    return service


@pytest.mark.asyncio
async def test_create_xero_invoice_reuses_existing_link(
    invoice,
    customer,
    connection,
    monkeypatch,
):
    service = build_service()

    invoice.xero_invoice_id = "xero-existing-id"

    service.invoices.get_by_id_for_update.return_value = invoice
    service.customers.get_by_id.return_value = customer

    async def fake_connection(*args, **kwargs):
        return connection

    monkeypatch.setattr(
        "apps.gpuaas.app.services.xero_invoice.get_valid_connection",
        fake_connection,
    )

    fake_client = SimpleNamespace(
        get_invoice=AsyncMock(
            return_value={
                "Invoices": [
                    {
                        "InvoiceID": "xero-existing-id",
                        "InvoiceNumber": invoice.invoice_number,
                    }
                ]
            }
        ),
    )

    monkeypatch.setattr(
        "apps.gpuaas.app.services.xero_invoice.XeroClient",
        lambda **kwargs: fake_client,
    )

    result = await service.create_xero_invoice(
        invoice.id,
    )

    fake_client.get_invoice.assert_awaited_once_with(
        "xero-existing-id",
    )

    assert result["Invoices"][0]["InvoiceID"] == "xero-existing-id"


@pytest.mark.asyncio
async def test_create_xero_invoice_recovers_existing_xero_invoice(
    invoice,
    customer,
    connection,
    monkeypatch,
):
    service = build_service()

    service.invoices.get_by_id_for_update.return_value = invoice
    service.customers.get_by_id.return_value = customer

    async def fake_connection(*args, **kwargs):
        return connection

    monkeypatch.setattr(
        "apps.gpuaas.app.services.xero_invoice.get_valid_connection",
        fake_connection,
    )

    fake_client = SimpleNamespace(
        get_organisation=AsyncMock(
            return_value={
                "Organisations": [
                    {
                        "BaseCurrency": "INR",
                    }
                ]
            }
        ),
        find_invoice_by_number=AsyncMock(
            return_value={
                "InvoiceID": "recovered-xero-id",
                "InvoiceNumber": invoice.invoice_number,
            }
        ),
        create_invoice=AsyncMock(),
    )

    monkeypatch.setattr(
        "apps.gpuaas.app.services.xero_invoice.XeroClient",
        lambda **kwargs: fake_client,
    )

    result = await service.create_xero_invoice(
        invoice.id,
    )

    fake_client.find_invoice_by_number.assert_awaited_once_with(
        invoice.invoice_number,
    )

    fake_client.create_invoice.assert_not_awaited()

    assert invoice.xero_invoice_id == "recovered-xero-id"
    assert result["Invoices"][0]["InvoiceID"] == "recovered-xero-id"


@pytest.mark.asyncio
async def test_create_xero_invoice_creates_and_persists_xero_id(
    invoice,
    customer,
    connection,
    monkeypatch,
):
    service = build_service()

    service.invoices.get_by_id_for_update.return_value = invoice
    service.customers.get_by_id.return_value = customer
    service.contacts.get_or_create_contact.return_value = "contact-id"

    async def fake_connection(*args, **kwargs):
        return connection

    monkeypatch.setattr(
        "apps.gpuaas.app.services.xero_invoice.get_valid_connection",
        fake_connection,
    )

    fake_client = SimpleNamespace(
        get_organisation=AsyncMock(
            return_value={
                "Organisations": [
                    {
                        "BaseCurrency": "INR",
                    }
                ]
            }
        ),
        find_invoice_by_number=AsyncMock(
            return_value=None,
        ),
        create_invoice=AsyncMock(
            return_value={
                "Invoices": [
                    {
                        "InvoiceID": "new-xero-id",
                        "InvoiceNumber": invoice.invoice_number,
                    }
                ]
            }
        ),
    )

    monkeypatch.setattr(
        "apps.gpuaas.app.services.xero_invoice.XeroClient",
        lambda **kwargs: fake_client,
    )

    result = await service.create_xero_invoice(
        invoice.id,
    )

    fake_client.create_invoice.assert_awaited_once()

    assert invoice.xero_invoice_id == "new-xero-id"
    assert result["Invoices"][0]["InvoiceID"] == "new-xero-id"

    service.session.flush.assert_awaited()


@pytest.mark.asyncio
async def test_create_xero_invoice_rejects_currency_mismatch(
    invoice,
    customer,
    connection,
    monkeypatch,
):
    service = build_service()

    invoice.currency = "USD"

    service.invoices.get_by_id_for_update.return_value = invoice
    service.customers.get_by_id.return_value = customer

    async def fake_connection(*args, **kwargs):
        return connection

    monkeypatch.setattr(
        "apps.gpuaas.app.services.xero_invoice.get_valid_connection",
        fake_connection,
    )

    fake_client = SimpleNamespace(
        get_organisation=AsyncMock(
            return_value={
                "Organisations": [
                    {
                        "BaseCurrency": "INR",
                    }
                ]
            }
        ),
        find_invoice_by_number=AsyncMock(),
        create_invoice=AsyncMock(),
    )

    monkeypatch.setattr(
        "apps.gpuaas.app.services.xero_invoice.XeroClient",
        lambda **kwargs: fake_client,
    )

    with pytest.raises(XeroInvoiceCurrencyError):
        await service.create_xero_invoice(
            invoice.id,
        )

    fake_client.find_invoice_by_number.assert_not_awaited()
    fake_client.create_invoice.assert_not_awaited()