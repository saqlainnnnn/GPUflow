from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.api.dependencies import get_db
from apps.gpuaas.app.schemas.job import JobCreate, JobResponse
from apps.gpuaas.app.services.job import (
    AllocationNotFoundError,
    AllocationOwnershipError,
    CustomerNotFoundError,
    JobAlreadyExistsError,
    JobCapacityError,
    JobNotFoundError,
    JobService,
)

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    data: JobCreate,
    session: AsyncSession = Depends(get_db),
) -> JobResponse:
    service = JobService(session)

    try:
        job = await service.create_job(data)
    except JobAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except AllocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except AllocationOwnershipError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except JobCapacityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return JobResponse.model_validate(job)


@router.get(
    "/{job_id}",
    response_model=JobResponse,
)
async def get_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> JobResponse:
    service = JobService(session)

    try:
        job = await service.get_job(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return JobResponse.model_validate(job)


@router.get(
    "/customer/{customer_id}",
    response_model=list[JobResponse],
)
async def list_customer_jobs(
    customer_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[JobResponse]:
    service = JobService(session)

    try:
        jobs = await service.list_customer_jobs(customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return [JobResponse.model_validate(job) for job in jobs]
