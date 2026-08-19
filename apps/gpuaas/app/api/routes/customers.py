from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.api.dependencies import get_db
from apps.gpuaas.app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
)
from apps.gpuaas.app.schemas.customer_identity import (
    CustomerIdentityCreate,
    CustomerIdentityResponse,
)
from apps.gpuaas.app.schemas.customer_reconciliation import (
    CustomerReconciliationRequest,
    CustomerReconciliationResponse,
)
from apps.gpuaas.app.services.customer_reconciliation_service import (
    CustomerReconciliationService,
)
from apps.gpuaas.app.services.customer_data_quality_persistence import (
    CustomerDataQualityPersistenceService,
)
from apps.gpuaas.app.services.customer_reconciliation_runner import (
    CustomerReconciliationRunner,
)
from apps.gpuaas.app.services.customer_field_ownership_provider import (
    CustomerFieldOwnershipProvider,
)
from apps.gpuaas.app.services.customer_reconciliation_factory import (
    CustomerReconciliationFactory,
)
from apps.gpuaas.app.repositories.customer_data_quality import (
    CustomerDataQualityRepository,
)
from apps.gpuaas.app.repositories.customer import (
    CustomerRepository,
)
from apps.gpuaas.app.repositories.customer_identity import (
    CustomerIdentityRepository,
)
from apps.gpuaas.app.schemas.customer_summary import (
    CustomerSummaryResponse,
)
from apps.gpuaas.app.schemas.customer_reconciliation_run import (
    CustomerReconciliationRunResponse,
)
from apps.gpuaas.app.services.customer import (
    CustomerAlreadyExistsError,
    CustomerNotFoundError,
    CustomerService,
)
from apps.gpuaas.app.services.customer_identity import (
    CustomerIdentityService,
)
from apps.gpuaas.app.services.customer_summary import (
    CustomerSummaryService,
)
from apps.gpuaas.app.repositories.customer_identity import (
    CustomerIdentityRepository,
)

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer(
    data: CustomerCreate,
    session: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    service = CustomerService(session)

    try:
        customer = await service.create_customer(data)
    except CustomerAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return CustomerResponse.model_validate(customer)


@router.put(
    "/by-external-id/{external_id}",
    response_model=CustomerResponse,
)
async def upsert_customer(
    external_id: str,
    data: CustomerCreate,
    session: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    if data.external_id != external_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("Path external_id must match payload external_id"),
        )

    service = CustomerService(session)

    customer, _ = await service.upsert_customer(data)

    return CustomerResponse.model_validate(customer)


@router.post(
    "/{customer_id}/identities",
    response_model=CustomerIdentityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def link_customer_identity(
    customer_id: UUID,
    data: CustomerIdentityCreate,
    session: AsyncSession = Depends(get_db),
) -> CustomerIdentityResponse:
    customer_service = CustomerService(session)

    try:
        await customer_service.get_customer(customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    repository = CustomerIdentityRepository(session)
    service = CustomerIdentityService(repository)

    try:
        identity = await service.link_identity(
            customer_id=customer_id,
            source=data.source,
            entity_type=data.entity_type,
            external_id=data.external_id,
        )
        await session.commit()
    except ValueError as exc:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return CustomerIdentityResponse.model_validate(identity)


@router.post(
    "/{customer_id}/reconciliation",
    response_model=CustomerReconciliationResponse,
)
async def reconcile_customer_source(
    customer_id: UUID,
    data: CustomerReconciliationRequest,
    session: AsyncSession = Depends(get_db),
) -> CustomerReconciliationResponse:
    customer_repository = CustomerRepository(session)
    identity_repository = CustomerIdentityRepository(session)
    quality_repository = CustomerDataQualityRepository(session)

    reconciler = CustomerReconciliationService(
        customer_repository=customer_repository,
        identity_repository=identity_repository,
    )

    persistence = CustomerDataQualityPersistenceService(
        repository=quality_repository,
    )

    runner = CustomerReconciliationRunner(
        reconciler=reconciler,
        persistence=persistence,
    )

    ownership_policy = (
        CustomerFieldOwnershipProvider()
        .for_customer()
    )

    class GenericSourceAdapter:
        def to_customer_record(
            self,
            source_record: dict,
        ) -> dict:
            return source_record

    try:
        result, _ = await runner.reconcile_and_persist(
            customer_id=customer_id,
            source=data.source,
            entity_type=data.entity_type,
            external_id=data.external_id,
            source_record=data.source_record,
            adapter=GenericSourceAdapter(),
            ownership_policy=ownership_policy,
        )

        await session.commit()

    except ValueError as exc:
        await session.rollback()

        detail = str(exc)

        status_code = (
            404
            if "not found" in detail.lower()
            else 409
        )

        raise HTTPException(
            status_code=status_code,
            detail=detail,
        ) from exc

    return CustomerReconciliationResponse(
        customer_id=customer_id,
        source=result.source,
        entity_type=result.entity_type,
        status=result.status.value,
        mismatches=result.mismatches,
        missing=result.missing,
        fields={
            field_name: {
                "status": field_result.status.value,
                "canonical_value": field_result.canonical_value,
                "source_value": field_result.source_value,
            }
            for field_name, field_result
            in result.fields.items()
        },
    )


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
)
async def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    session: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    service = CustomerService(session)

    try:
        customer = await service.update_customer(
            customer_id,
            data,
        )
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return CustomerResponse.model_validate(customer)


@router.get(
    "",
    response_model=list[CustomerResponse],
)
async def list_customers(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
) -> list[CustomerResponse]:
    service = CustomerService(session)

    customers = await service.list_customers(
        offset=offset,
        limit=limit,
    )

    return [CustomerResponse.model_validate(customer) for customer in customers]


@router.get(
    "/{customer_id}/summary",
    response_model=CustomerSummaryResponse,
)
async def get_customer_summary(
    customer_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> CustomerSummaryResponse:
    service = CustomerSummaryService(session)

    try:
        return await service.get_summary(customer_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
async def get_customer(
    customer_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    service = CustomerService(session)

    try:
        customer = await service.get_customer(customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return CustomerResponse.model_validate(customer)


@router.post(
    "/reconciliation/runs",
    response_model=CustomerReconciliationRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def trigger_customer_reconciliation_run(
    session: AsyncSession = Depends(get_db),
) -> CustomerReconciliationRunResponse:
    factory = CustomerReconciliationFactory(
        session=session,
    )

    run_service = factory.build_run_service()

    run = await run_service.run()

    return CustomerReconciliationRunResponse.model_validate(
        run
    )
