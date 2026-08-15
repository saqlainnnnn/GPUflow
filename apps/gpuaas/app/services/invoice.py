from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.core.pricing import get_gpu_hourly_rate
from apps.gpuaas.app.models.invoice import Invoice
from apps.gpuaas.app.models.invoice_line_item import InvoiceLineItem
from apps.gpuaas.app.repositories.customer import CustomerRepository
from apps.gpuaas.app.repositories.invoice import InvoiceRepository
from apps.gpuaas.app.repositories.usage_event import UsageEventRepository


class CustomerNotFoundError(Exception):
    pass


class InvoiceNotFoundError(Exception):
    pass


class InvalidInvoiceStatusError(Exception):
    pass


class InvoiceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.customers = CustomerRepository(session)
        self.invoices = InvoiceRepository(session)
        self.usage = UsageEventRepository(session)

    async def create_invoice(
        self,
        customer_id: UUID,
        period_start: date,
        period_end: date,
    ) -> Invoice:
        customer = await self.customers.get_by_id(customer_id)

        if customer is None:
            raise CustomerNotFoundError(f"Customer '{customer_id}' not found")

        existing = await self.invoices.get_by_customer_period(
            customer_id,
            period_start,
            period_end,
        )

        if existing is not None:
            return existing

        events = await self.usage.list_by_customer(
            customer_id=customer_id,
            start=period_start,
            end=period_end,
        )

        invoice = Invoice(
            customer_id=customer_id,
            invoice_number=(
                f"INV-{period_start:%Y%m%d}-{period_end:%Y%m%d}-{str(customer_id)[:8].upper()}"
            ),
            period_start=period_start,
            period_end=period_end,
            currency="USD",
            subtotal=Decimal("0.00"),
            total=Decimal("0.00"),
            status="draft",
        )

        subtotal = Decimal("0.00")

        for event in events:
            rate = get_gpu_hourly_rate(event.gpu_type)

            gpu_hours = Decimal(str(event.gpu_hours))

            amount = (gpu_hours * rate).quantize(Decimal("0.01"))

            invoice.line_items.append(
                InvoiceLineItem(
                    description=(f"{event.gpu_type} GPU usage"),
                    gpu_type=event.gpu_type,
                    gpu_hours=gpu_hours,
                    rate_per_gpu_hour=rate,
                    amount=amount,
                )
            )

            subtotal += amount

        invoice.subtotal = subtotal
        invoice.total = subtotal

        try:
            await self.invoices.create(invoice)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()

            existing = await self.invoices.get_by_customer_period(
                customer_id,
                period_start,
                period_end,
            )

            if existing is None:
                raise

            return existing

        return invoice

    async def get_invoice(
        self,
        invoice_id: UUID,
    ) -> Invoice:
        invoice = await self.invoices.get_by_id(invoice_id)

        if invoice is None:
            raise InvoiceNotFoundError(f"Invoice '{invoice_id}' not found")

        return invoice

    async def list_customer_invoices(
        self,
        customer_id: UUID,
    ) -> list[Invoice]:
        customer = await self.customers.get_by_id(customer_id)

        if customer is None:
            raise CustomerNotFoundError(f"Customer '{customer_id}' not found")

        return await self.invoices.list_by_customer(customer_id)

    async def update_status(
        self,
        invoice_id: UUID,
        new_status: str,
    ) -> Invoice:
        invoice = await self.get_invoice(invoice_id)

        allowed = {
            "draft",
            "issued",
            "paid",
        }

        if new_status not in allowed:
            raise InvalidInvoiceStatusError(f"Invalid invoice status '{new_status}'")

        if invoice.status == "paid" and new_status != "paid":
            raise InvalidInvoiceStatusError("Paid invoices cannot move backwards")

        if invoice.status == "issued" and new_status == "draft":
            raise InvalidInvoiceStatusError("Issued invoices cannot return to draft")

        invoice.status = new_status

        await self.session.commit()
        await self.session.refresh(invoice)

        return invoice
