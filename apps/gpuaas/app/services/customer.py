from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.customer import Customer
from apps.gpuaas.app.repositories.customer import CustomerRepository
from apps.gpuaas.app.schemas.customer import CustomerCreate


class CustomerAlreadyExistsError(Exception):
    pass


class CustomerNotFoundError(Exception):
    pass


class CustomerService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = CustomerRepository(session)
        self.session = session

    async def create_customer(self, data: CustomerCreate) -> Customer:
        existing = await self.repository.get_by_external_id(data.external_id)

        if existing is not None:
            raise CustomerAlreadyExistsError(
                f"Customer with external_id '{data.external_id}' already exists"
            )

        customer = Customer(
            external_id=data.external_id,
            company_name=data.company_name,
            email=str(data.email),
            country=data.country.upper(),
            status=data.status,
        )

        try:
            customer = await self.repository.create(customer)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise CustomerAlreadyExistsError(
                f"Customer with external_id '{data.external_id}' already exists"
            ) from exc

        return customer

    async def get_customer(self, customer_id: UUID) -> Customer:
        customer = await self.repository.get_by_id(customer_id)

        if customer is None:
            raise CustomerNotFoundError(f"Customer '{customer_id}' not found")

        return customer

    async def list_customers(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Customer]:
        return await self.repository.list(
            offset=offset,
            limit=limit,
        )
