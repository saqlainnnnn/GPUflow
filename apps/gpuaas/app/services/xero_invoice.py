from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.integrations.xero.client import XeroClient
from apps.gpuaas.app.integrations.xero.token_manager import (
    get_valid_connection,
)
from apps.gpuaas.app.repositories.customer import CustomerRepository
from apps.gpuaas.app.repositories.invoice import InvoiceRepository
from apps.gpuaas.app.services.xero_contact import XeroContactService


class XeroInvoiceCurrencyError(Exception):
    pass


class XeroInvoiceService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session
        self.invoices = InvoiceRepository(session)
        self.customers = CustomerRepository(session)
        self.contacts = XeroContactService(session)

    @staticmethod
    def _extract_invoice_id(
        response: dict[str, Any],
    ) -> str:
        invoices = response.get(
            "Invoices",
            [],
        )

        if not invoices:
            raise RuntimeError(
                "Xero invoice response contained no invoices"
            )

        invoice_id = invoices[0].get("InvoiceID")

        if not invoice_id:
            raise RuntimeError(
                "Xero invoice response missing InvoiceID"
            )

        return str(invoice_id)

    async def create_xero_invoice(
        self,
        invoice_id: UUID,
    ) -> dict[str, Any]:
        invoice = await self.invoices.get_by_id_for_update(
            invoice_id,
        )

        if invoice is None:
            raise ValueError(
                f"Invoice '{invoice_id}' not found"
            )

        customer = await self.customers.get_by_id(
            invoice.customer_id,
        )

        if customer is None:
            raise ValueError(
                f"Customer '{invoice.customer_id}' not found"
            )

        connection = await get_valid_connection(
            self.session,
            invoice.customer_id,
        )

        client = XeroClient(
            access_token=connection.access_token,
            tenant_id=connection.tenant_id,
        )

        # Fast path:
        # GPUFlow already knows which Xero invoice represents this invoice.
        if invoice.xero_invoice_id:
            return await client.get_invoice(
                invoice.xero_invoice_id,
            )

        organisation_response = await client.get_organisation()

        organisations = organisation_response.get(
            "Organisations",
            [],
        )

        if not organisations:
            raise RuntimeError(
                "Xero organisation response contained no organisation"
            )

        xero_currency = organisations[0].get(
            "BaseCurrency",
        )

        if not xero_currency:
            raise RuntimeError(
                "Xero organisation response missing BaseCurrency"
            )

        if invoice.currency != xero_currency:
            raise XeroInvoiceCurrencyError(
                f"GPUFlow invoice currency '{invoice.currency}' "
                f"does not match Xero organisation currency "
                f"'{xero_currency}'"
            )

        # Recovery path:
        # Xero may already contain the invoice if the previous request
        # succeeded at Xero but failed before GPUFlow persisted the ID.
        existing_xero_invoice = await client.find_invoice_by_number(
            invoice.invoice_number,
        )

        if existing_xero_invoice is not None:
            existing_invoice_id = existing_xero_invoice.get(
                "InvoiceID",
            )

            if not existing_invoice_id:
                raise RuntimeError(
                    "Existing Xero invoice response missing InvoiceID"
                )

            invoice.xero_invoice_id = str(
                existing_invoice_id,
            )

            await self.session.flush()

            return {
                "Invoices": [existing_xero_invoice],
            }

        contact_id = await self.contacts.get_or_create_contact(
            invoice.customer_id,
        )

        line_items: list[dict[str, Any]] = []

        for item in invoice.line_items:
            line_items.append(
                {
                    "Description": item.description,
                    "Quantity": float(item.gpu_hours),
                    "UnitAmount": float(
                        item.rate_per_gpu_hour,
                    ),
                    "AccountCode": "400",
                }
            )

        payload = {
            "Type": "ACCREC",
            "Contact": {
                "ContactID": contact_id,
            },
            "Date": invoice.period_end.isoformat(),
            "DueDate": invoice.period_end.isoformat(),
            "InvoiceNumber": invoice.invoice_number,
            "Reference": (
                f"GPUFlow invoice {invoice.invoice_number}"
            ),
            "CurrencyCode": xero_currency,
            "LineAmountTypes": "Exclusive",
            "LineItems": line_items,
            "Status": "DRAFT",
        }

        response = await client.create_invoice(
            payload,
        )

        created_invoice_id = self._extract_invoice_id(
            response,
        )

        invoice.xero_invoice_id = created_invoice_id

        await self.session.flush()

        return response