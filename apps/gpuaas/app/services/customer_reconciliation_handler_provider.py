from typing import Any

from apps.gpuaas.app.services.customer_reconciliation_handler_registry import (
    CustomerReconciliationHandlerRegistry,
)


class CustomerReconciliationHandlerProvider:
    def __init__(
        self,
        *,
        registry: CustomerReconciliationHandlerRegistry,
        pipedrive_handler: Any,
        xero_handler: Any,
    ) -> None:
        self.registry = registry
        self.pipedrive_handler = pipedrive_handler
        self.xero_handler = xero_handler

    def register_defaults(self) -> None:
        self.registry.register(
            source="pipedrive",
            entity_type="organization",
            handler=self.pipedrive_handler,
        )

        self.registry.register(
            source="xero",
            entity_type="contact",
            handler=self.xero_handler,
        )
