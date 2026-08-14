from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.job import GPUJob


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, job: GPUJob) -> GPUJob:
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        return job

    async def get_by_id(self, job_id: UUID) -> GPUJob | None:
        result = await self.session.execute(select(GPUJob).where(GPUJob.id == job_id))
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str) -> GPUJob | None:
        result = await self.session.execute(select(GPUJob).where(GPUJob.external_id == external_id))
        return result.scalar_one_or_none()

    async def list_by_customer(
        self,
        customer_id: UUID,
    ) -> list[GPUJob]:
        result = await self.session.execute(
            select(GPUJob)
            .where(GPUJob.customer_id == customer_id)
            .order_by(GPUJob.created_at.desc())
        )
        return list(result.scalars().all())
