from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.invoice import Invoice


class InvoiceRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create(
        self,
        invoice: Invoice,
    ) -> Invoice:
        self.session.add(invoice)
        await self.session.flush()
        await self.session.refresh(invoice)

        return invoice

    async def get_by_id(
        self,
        invoice_id: UUID,
    ) -> Invoice | None:
        result = await self.session.execute(
            select(Invoice).where(
                Invoice.id == invoice_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_id_for_update(
        self,
        invoice_id: UUID,
    ) -> Invoice | None:
        result = await self.session.execute(
            select(Invoice)
            .where(
                Invoice.id == invoice_id,
            )
            .with_for_update()
        )

        return result.scalar_one_or_none()

    async def get_by_customer_period(
        self,
        customer_id: UUID,
        period_start: date,
        period_end: date,
    ) -> Invoice | None:
        result = await self.session.execute(
            select(Invoice).where(
                Invoice.customer_id == customer_id,
                Invoice.period_start == period_start,
                Invoice.period_end == period_end,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_xero_invoice_id(
        self,
        xero_invoice_id: str,
    ) -> Invoice | None:
        result = await self.session.execute(
            select(Invoice).where(
                Invoice.xero_invoice_id == xero_invoice_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_by_customer(
        self,
        customer_id: UUID,
    ) -> list[Invoice]:
        result = await self.session.execute(
            select(Invoice)
            .where(
                Invoice.customer_id == customer_id,
            )
            .order_by(
                Invoice.created_at.desc(),
            )
        )

        return list(result.scalars().all())