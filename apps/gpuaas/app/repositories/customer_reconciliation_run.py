from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.customer_reconciliation_run import (
    CustomerReconciliationRun,
)


class CustomerReconciliationRunRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create(
        self,
        run: CustomerReconciliationRun,
    ) -> CustomerReconciliationRun:
        self.session.add(run)

        await self.session.flush()
        await self.session.refresh(run)

        return run

    async def get(
        self,
        run_id: UUID,
    ) -> CustomerReconciliationRun | None:
        result = await self.session.execute(
            select(CustomerReconciliationRun).where(
                CustomerReconciliationRun.id == run_id
            )
        )

        return result.scalar_one_or_none()

    async def update(
        self,
        run: CustomerReconciliationRun,
    ) -> CustomerReconciliationRun:
        await self.session.flush()
        await self.session.refresh(run)

        return run

    async def get_latest(
        self,
    ) -> CustomerReconciliationRun | None:
        result = await self.session.execute(
            select(CustomerReconciliationRun)
            .order_by(
                CustomerReconciliationRun.started_at.desc()
            )
            .limit(1)
        )

        return result.scalar_one_or_none()
