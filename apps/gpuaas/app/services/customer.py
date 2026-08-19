from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.integrations.events import (
    build_customer_updated_event,
)
from apps.gpuaas.app.models.customer import Customer
from apps.gpuaas.app.models.kyb_audit import KYBAudit
from apps.gpuaas.app.repositories.customer import CustomerRepository
from apps.gpuaas.app.repositories.outbox import OutboxRepository
from apps.gpuaas.app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
)
from apps.gpuaas.app.services.kyb import (
    KYBDecision,
    KYBScreeningService,
)
from apps.gpuaas.app.services.kyb_audit import (
    KYBAuditService,
)


class CustomerAlreadyExistsError(Exception):
    pass


class CustomerNotFoundError(Exception):
    pass


class CustomerService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        kyb: KYBScreeningService | None = None,
        kyb_audit: KYBAuditService | None = None,
    ) -> None:
        self.repository = CustomerRepository(session)
        self.outbox = OutboxRepository(session)
        self.session = session
        self.kyb = kyb or KYBScreeningService()
        self.kyb_audit = kyb_audit

    async def create_customer(
        self,
        data: CustomerCreate,
    ) -> Customer:
        existing = await self.repository.get_by_external_id(data.external_id)

        if existing is not None:
            raise CustomerAlreadyExistsError(
                f"Customer with external_id '{data.external_id}' already exists"
            )

        screening = self.kyb.screen_customer(
            company_name=data.company_name,
            country=data.country,
        )

        activation_status = {
            KYBDecision.CLEAR: "active",
            KYBDecision.FLAGGED: "pending_review",
            KYBDecision.BLOCKED: "blocked",
        }[screening.decision]

        customer = Customer(
            external_id=data.external_id,
            company_name=data.company_name,
            email=str(data.email),
            country=data.country.upper(),
            status=activation_status,
        )

        try:
            customer = await self.repository.create(customer)

            if self.kyb_audit is not None:
                await self.kyb_audit.record_screening(
                    customer_id=customer.id,
                    company_name=data.company_name,
                    country=data.country.upper(),
                    result=screening,
                )

            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise CustomerAlreadyExistsError(
                f"Customer with external_id '{data.external_id}' already exists"
            ) from exc

        return customer

    async def upsert_customer(
        self,
        data: CustomerCreate,
    ) -> tuple[Customer, bool]:
        existing = await self.repository.get_by_external_id(data.external_id)

        if existing is None:
            activation_status = self._activation_status(
                company_name=data.company_name,
                country=data.country,
            )

            customer = Customer(
                external_id=data.external_id,
                company_name=data.company_name,
                email=str(data.email),
                country=data.country.upper(),
                status=activation_status,
            )

            try:
                customer = await self.repository.create(customer)
                await self.session.commit()
            except IntegrityError:
                await self.session.rollback()

                existing = await self.repository.get_by_external_id(data.external_id)

                if existing is None:
                    raise

                customer = await self.repository.update(
                    existing,
                    company_name=data.company_name,
                    email=str(data.email),
                    country=data.country,
                    status=data.status,
                )

                await self.session.commit()

            return customer, True

        customer = await self.repository.update(
            existing,
            company_name=data.company_name,
            email=str(data.email),
            country=data.country,
            status=data.status,
        )

        await self.session.commit()

        return customer, False

    async def update_customer(
        self,
        customer_id: UUID,
        data: CustomerUpdate,
    ) -> Customer:
        customer = await self.repository.get_by_id(customer_id)

        if customer is None:
            raise CustomerNotFoundError(f"Customer '{customer_id}' not found")

        customer = await self.repository.update(
            customer,
            company_name=data.company_name,
            email=str(data.email),
            country=data.country,
            status=data.status,
        )

        if data.sync_origin == "gpuaas":
            event = build_customer_updated_event(
                customer.id,
                external_id=customer.external_id,
                company_name=customer.company_name,
                email=customer.email,
                country=customer.country,
                sync_origin=data.sync_origin,
            )

            await self.outbox.create(
                aggregate_type="customer",
                aggregate_id=customer.id,
                event_type="customer.updated",
                payload=event,
            )

        await self.session.commit()

        return customer

    async def get_customer(
        self,
        customer_id: UUID,
    ) -> Customer:
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

    async def review_kyb(
        self,
        *,
        customer_id: UUID,
        decision: str,
        reviewer: str,
    ) -> Customer:
        customer = await self.repository.get_by_id(
            customer_id
        )

        if customer is None:
            raise CustomerNotFoundError(
                f"Customer '{customer_id}' not found"
            )

        if customer.status != "pending_review":
            raise ValueError(
                "Customer is not pending KYB review"
            )

        customer = await self.repository.update(
            customer,
            company_name=customer.company_name,
            email=customer.email,
            country=customer.country,
            status=(
                "active"
                if decision == "approve"
                else "blocked"
            ),
        )

        audit = KYBAudit(
            customer_id=customer.id,
            check_type="human_review",
            input_snapshot={
                "company_name": customer.company_name,
                "country": customer.country,
                "previous_status": "pending_review",
            },
            decision=(
                "approved"
                if decision == "approve"
                else "rejected"
            ),
            reason=(
                f"KYB review {decision}d by {reviewer}"
            ),
            reviewer=reviewer,
        )

        self.session.add(audit)

        await self.session.commit()
        await self.session.refresh(customer)

        return customer

