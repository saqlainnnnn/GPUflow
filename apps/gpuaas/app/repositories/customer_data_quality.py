from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.customer_data_quality import (
    CustomerDataQualityRecord,
)


class CustomerDataQualityRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def find_for_identity(
        self,
        *,
        customer_id: UUID,
        source: str,
        entity_type: str,
        external_id: str,
    ) -> CustomerDataQualityRecord | None:
        result = await self.session.execute(
            select(CustomerDataQualityRecord).where(
                CustomerDataQualityRecord.customer_id == customer_id,
                CustomerDataQualityRecord.source == source,
                CustomerDataQualityRecord.entity_type == entity_type,
                CustomerDataQualityRecord.external_id == external_id,
            )
        )

        return result.scalar_one_or_none()

    async def find_for_customer(
        self,
        customer_id: UUID,
    ) -> list[CustomerDataQualityRecord]:
        result = await self.session.execute(
            select(CustomerDataQualityRecord)
            .where(
                CustomerDataQualityRecord.customer_id == customer_id
            )
            .order_by(
                CustomerDataQualityRecord.checked_at.desc()
            )
        )

        return list(result.scalars().all())

    async def create(
        self,
        record: CustomerDataQualityRecord,
    ) -> CustomerDataQualityRecord:
        self.session.add(record)

        await self.session.flush()
        await self.session.refresh(record)

        return record
