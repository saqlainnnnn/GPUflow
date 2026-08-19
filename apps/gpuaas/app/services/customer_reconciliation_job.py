from apps.gpuaas.app.repositories.customer_identity import (
    CustomerIdentityRepository,
)
from apps.gpuaas.app.services.customer_reconciliation_handler_registry import (
    CustomerReconciliationHandlerRegistry,
)


class CustomerReconciliationJob:
    def __init__(
        self,
        *,
        identity_repository: CustomerIdentityRepository,
        registry: CustomerReconciliationHandlerRegistry,
    ) -> None:
        self.identities = identity_repository
        self.registry = registry

    async def run(self) -> dict[str, int]:
        identities = await self.identities.find_all()

        processed = 0
        succeeded = 0
        failed = 0

        for identity in identities:
            processed += 1

            handler = self.registry.get(
                source=identity.source,
                entity_type=identity.entity_type,
            )

            if handler is None:
                failed += 1
                continue

            try:
                await handler.reconcile(identity)

            except Exception:
                failed += 1

            else:
                succeeded += 1

        return {
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
        }
