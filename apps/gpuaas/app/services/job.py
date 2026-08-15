from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.models.job import GPUJob
from apps.gpuaas.app.repositories.allocation import AllocationRepository
from apps.gpuaas.app.repositories.customer import CustomerRepository
from apps.gpuaas.app.repositories.job import JobRepository
from apps.gpuaas.app.schemas.job import (
    JobComplete,
    JobCreate,
    JobFail,
)
from apps.gpuaas.app.schemas.usage_event import UsageEventCreate
from apps.gpuaas.app.services.usage_event import UsageEventService


class JobNotFoundError(Exception):
    pass


class JobAlreadyExistsError(Exception):
    pass


class CustomerNotFoundError(Exception):
    pass


class AllocationNotFoundError(Exception):
    pass


class AllocationOwnershipError(Exception):
    pass


class JobCapacityError(Exception):
    pass


class InvalidJobStateError(Exception):
    pass


class JobService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.jobs = JobRepository(session)
        self.customers = CustomerRepository(session)
        self.allocations = AllocationRepository(session)
        self.usage = UsageEventService(session)

    async def create_job(
        self,
        data: JobCreate,
    ) -> GPUJob:
        existing = await self.jobs.get_by_external_id(data.external_id)

        if existing is not None:
            raise JobAlreadyExistsError(f"Job with external_id '{data.external_id}' already exists")

        customer = await self.customers.get_by_id(data.customer_id)

        if customer is None:
            raise CustomerNotFoundError(f"Customer '{data.customer_id}' not found")

        allocation = await self.allocations.get_by_id(data.allocation_id)

        if allocation is None:
            raise AllocationNotFoundError(f"Allocation '{data.allocation_id}' not found")

        if allocation.customer_id != data.customer_id:
            raise AllocationOwnershipError("Allocation does not belong to the specified customer")

        if data.gpu_count > allocation.gpu_count:
            raise JobCapacityError(
                f"Job requested {data.gpu_count} GPUs but "
                f"allocation contains only "
                f"{allocation.gpu_count}"
            )

        if data.status != "pending":
            raise InvalidJobStateError("New jobs must start in pending state")

        job = GPUJob(
            external_id=data.external_id,
            customer_id=data.customer_id,
            allocation_id=data.allocation_id,
            gpu_type=allocation.gpu_type,
            gpu_count=data.gpu_count,
            status="pending",
            duration_seconds=0,
            failure_reason=None,
        )

        await self.jobs.create(job)
        await self.session.commit()

        return job

    async def start_job(
        self,
        job_id: UUID,
    ) -> GPUJob:
        job = await self._get_job(job_id)

        if job.status != "pending":
            raise InvalidJobStateError(f"Job '{job_id}' cannot start from status '{job.status}'")

        job.status = "running"
        job.failure_reason = None

        await self.session.commit()
        await self.session.refresh(job)

        return job

    async def complete_job(
        self,
        job_id: UUID,
        data: JobComplete,
    ) -> GPUJob:
        job = await self._get_job(job_id)

        if job.status != "running":
            raise InvalidJobStateError(f"Job '{job_id}' cannot complete from status '{job.status}'")

        job.status = "completed"
        job.duration_seconds = data.duration_seconds
        job.failure_reason = None

        gpu_hours = job.gpu_count * data.duration_seconds / 3600

        usage_event = UsageEventCreate(
            event_id=f"job:{job.id}:completed",
            customer_id=job.customer_id,
            allocation_id=job.allocation_id,
            gpu_type=job.gpu_type,
            gpu_hours=gpu_hours,
            utilization=1.0,
            timestamp=datetime.now(UTC),
        )

        await self.usage.create_event(usage_event)

        # Commit the job update and usage event together.
        await self.session.commit()
        await self.session.refresh(job)

        return job

    async def fail_job(
        self,
        job_id: UUID,
        data: JobFail,
    ) -> GPUJob:
        job = await self._get_job(job_id)

        if job.status != "running":
            raise InvalidJobStateError(f"Job '{job_id}' cannot fail from status '{job.status}'")

        job.status = "failed"
        job.failure_reason = data.failure_reason

        await self.session.commit()
        await self.session.refresh(job)

        return job

    async def get_job(
        self,
        job_id: UUID,
    ) -> GPUJob:
        return await self._get_job(job_id)

    async def list_customer_jobs(
        self,
        customer_id: UUID,
    ) -> list[GPUJob]:
        customer = await self.customers.get_by_id(customer_id)

        if customer is None:
            raise CustomerNotFoundError(f"Customer '{customer_id}' not found")

        return await self.jobs.list_by_customer(customer_id)

    async def _get_job(
        self,
        job_id: UUID,
    ) -> GPUJob:
        job = await self.jobs.get_by_id(job_id)

        if job is None:
            raise JobNotFoundError(f"Job '{job_id}' not found")

        return job
