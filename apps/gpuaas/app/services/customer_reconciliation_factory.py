from typing import Any

from apps.integration_hub.app.integrations.pipedrive.reconciliation import (
    PipedriveOrganizationReconciliationAdapter,
)
from apps.gpuaas.app.repositories.customer import (
    CustomerRepository,
)
from apps.gpuaas.app.repositories.customer_data_quality import (
    CustomerDataQualityRepository,
)
from apps.gpuaas.app.repositories.customer_data_quality_audit import (
    CustomerDataQualityAuditRepository,
)
from apps.gpuaas.app.repositories.customer_identity import (
    CustomerIdentityRepository,
)
from apps.gpuaas.app.repositories.customer_reconciliation_run import (
    CustomerReconciliationRunRepository,
)
from apps.gpuaas.app.services.customer_data_quality_persistence import (
    CustomerDataQualityPersistenceService,
)
from apps.gpuaas.app.services.customer_conflict_resolution import (
    CustomerConflictResolutionService,
)
from apps.gpuaas.app.services.customer_field_ownership_provider import (
    CustomerFieldOwnershipProvider,
)
from apps.gpuaas.app.services.customer_reconciliation_handler_provider import (
    CustomerReconciliationHandlerProvider,
)
from apps.gpuaas.app.services.customer_reconciliation_handler_registry import (
    CustomerReconciliationHandlerRegistry,
)
from apps.gpuaas.app.services.customer_reconciliation_job import (
    CustomerReconciliationJob,
)
from apps.gpuaas.app.services.customer_reconciliation_runner import (
    CustomerReconciliationRunner,
)
from apps.gpuaas.app.services.customer_reconciliation_run_service import (
    CustomerReconciliationRunService,
)
from apps.gpuaas.app.services.customer_reconciliation_service import (
    CustomerReconciliationService,
)
from apps.gpuaas.app.services.pipedrive_customer_reconciliation_handler import (
    PipedriveCustomerReconciliationHandler,
)
from apps.gpuaas.app.services.xero_customer_reconciliation_handler import (
    XeroCustomerReconciliationHandler,
)
from apps.gpuaas.app.services.xero_reconciliation import (
    XeroContactReconciliationAdapter,
)
from apps.integration_hub.app.integrations.pipedrive.client import (
    get_pipedrive_client,
)


class CustomerReconciliationFactory:
    def __init__(
        self,
        *,
        session: Any,
    ) -> None:
        self.session = session

    def build_registry(
        self,
    ) -> CustomerReconciliationHandlerRegistry:
        customer_repository = CustomerRepository(
            self.session
        )

        identity_repository = CustomerIdentityRepository(
            self.session
        )

        quality_repository = CustomerDataQualityRepository(
            self.session
        )

        reconciler = CustomerReconciliationService(
            customer_repository=customer_repository,
            identity_repository=identity_repository,
        )

        persistence = (
            CustomerDataQualityPersistenceService(
                repository=quality_repository
            )
        )

        audit_repository = CustomerDataQualityAuditRepository(
            self.session
        )

        conflict_resolution = (
            CustomerConflictResolutionService(
                audit_repository=audit_repository,
            )
        )

        runner = CustomerReconciliationRunner(
            reconciler=reconciler,
            persistence=persistence,
            conflict_resolution=conflict_resolution,
        )

        ownership_policy = (
            CustomerFieldOwnershipProvider()
            .for_customer()
        )

        registry = (
            CustomerReconciliationHandlerRegistry()
        )

        pipedrive_handler = (
            PipedriveCustomerReconciliationHandler(
                pipedrive=get_pipedrive_client(),
                adapter=(
                    PipedriveOrganizationReconciliationAdapter()
                ),
                runner=runner,
                ownership_policy=ownership_policy,
            )
        )

        xero_handler = (
            XeroCustomerReconciliationHandler(
                session=self.session,
                adapter=(
                    XeroContactReconciliationAdapter()
                ),
                runner=runner,
                ownership_policy=ownership_policy,
            )
        )

        provider = (
            CustomerReconciliationHandlerProvider(
                registry=registry,
                pipedrive_handler=pipedrive_handler,
                xero_handler=xero_handler,
            )
        )

        provider.register_defaults()

        return registry

    def build_job(
        self,
    ) -> CustomerReconciliationJob:
        registry = self.build_registry()

        identity_repository = (
            CustomerIdentityRepository(
                self.session
            )
        )

        return CustomerReconciliationJob(
            identity_repository=identity_repository,
            registry=registry,
        )

    def build_run_service(
        self,
    ) -> CustomerReconciliationRunService:
        job = self.build_job()

        repository = (
            CustomerReconciliationRunRepository(
                self.session
            )
        )

        return CustomerReconciliationRunService(
            repository=repository,
            job=job,
        )
