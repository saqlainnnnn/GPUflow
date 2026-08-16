from typing import Protocol
from uuid import UUID

from apps.ai.tools.schemas import (
    GetJobsInput,
    JobToolOutput,
)


class JobServiceProtocol(Protocol):
    async def list_customer_jobs(
        self,
        customer_id: UUID,
    ): ...


class JobCustomerNotFoundError(Exception):
    pass


class JobTool:
    def __init__(
        self,
        job_service: JobServiceProtocol,
    ) -> None:
        self.job_service = job_service

    async def get_jobs(
        self,
        data: GetJobsInput,
    ) -> list[JobToolOutput]:
        from apps.gpuaas.app.services.job import (
            CustomerNotFoundError,
        )

        try:
            jobs = await self.job_service.list_customer_jobs(
                data.customer_id,
            )
        except CustomerNotFoundError as exc:
            raise JobCustomerNotFoundError(
                f"Customer '{data.customer_id}' not found",
            ) from exc

        return [
            JobToolOutput(
                id=job.id,
                external_id=job.external_id,
                customer_id=job.customer_id,
                allocation_id=job.allocation_id,
                gpu_type=job.gpu_type,
                gpu_count=job.gpu_count,
                status=job.status,
                duration_seconds=job.duration_seconds,
                failure_reason=job.failure_reason,
            )
            for job in jobs
        ]
