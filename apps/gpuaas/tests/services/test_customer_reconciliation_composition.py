from unittest.mock import MagicMock

from apps.gpuaas.app.services.customer_reconciliation_handler_registry import (
    CustomerReconciliationHandlerRegistry,
)
from apps.gpuaas.app.services.customer_reconciliation_handler_provider import (
    CustomerReconciliationHandlerProvider,
)


def test_provider_registers_real_source_handlers():
    registry = CustomerReconciliationHandlerRegistry()

    pipedrive_handler = MagicMock()
    xero_handler = MagicMock()

    provider = CustomerReconciliationHandlerProvider(
        registry=registry,
        pipedrive_handler=pipedrive_handler,
        xero_handler=xero_handler,
    )

    provider.register_defaults()

    assert registry.get(
        source="pipedrive",
        entity_type="organization",
    ) is pipedrive_handler

    assert registry.get(
        source="xero",
        entity_type="contact",
    ) is xero_handler


def test_provider_does_not_register_unsupported_sources():
    registry = CustomerReconciliationHandlerRegistry()

    provider = CustomerReconciliationHandlerProvider(
        registry=registry,
        pipedrive_handler=MagicMock(),
        xero_handler=MagicMock(),
    )

    provider.register_defaults()

    assert registry.get(
        source="hubspot",
        entity_type="company",
    ) is None
