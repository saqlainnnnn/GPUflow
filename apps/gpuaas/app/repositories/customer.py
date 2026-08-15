from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.customer import Customer


class CustomerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        customer: Customer,
    ) -> Customer:
        self.session.add(customer)
        await self.session.flush()
        await self.session.refresh(customer)
        return customer

    async def get_by_id(
        self,
        customer_id: UUID,
    ) -> Customer | None:
        result = await self.session.execute(select(Customer).where(Customer.id == customer_id))
        return result.scalar_one_or_none()

    async def get_by_external_id(
        self,
        external_id: str,
    ) -> Customer | None:
        result = await self.session.execute(
            select(Customer).where(Customer.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        customer: Customer,
        *,
        company_name: str,
        email: str,
        country: str,
        status: str,
    ) -> Customer:
        customer.company_name = company_name
        customer.email = email
        customer.country = country.upper()
        customer.status = status

        await self.session.flush()
        await self.session.refresh(customer)

        return customer

    async def list(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Customer]:
        result = await self.session.execute(
            select(Customer).order_by(Customer.created_at.desc()).offset(offset).limit(limit)
        )

        return list(result.scalars().all())
