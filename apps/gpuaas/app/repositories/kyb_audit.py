from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.kyb_audit import KYBAudit


class KYBAuditRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create(
        self,
        audit: KYBAudit,
    ) -> KYBAudit:
        self.session.add(audit)
        await self.session.flush()
        await self.session.refresh(audit)
        return audit

    async def list_for_customer(
        self,
        customer_id: UUID,
    ) -> list[KYBAudit]:
        result = await self.session.execute(
            select(KYBAudit)
            .where(
                KYBAudit.customer_id == customer_id
            )
            .order_by(
                KYBAudit.timestamp.desc()
            )
        )

        return list(result.scalars().all())
