from unittest.mock import MagicMock

import pytest

from apps.gpuaas.app.services.customer_reconciliation_handler_registry import (
    CustomerReconciliationHandlerRegistry,
)
from apps.gpuaas.app.services.customer_reconciliation_handler_provider import (
    CustomerReconciliationHandlerProvider,
)


def test_provider_registers_pipedrive_handler():
    registry = CustomerReconciliationHandlerRegistry()

    pipedrive_handler = MagicMock()
    xero_handler = MagicMock()

    provider = CustomerReconciliationHandlerProvider(
        registry=registry,
        pipedrive_handler=pipedrive_handler,
        xero_handler=xero_handler,
    )

    provider.register_defaults()

    assert (
        registry.get(
            source="pipedrive",
            entity_type="organization",
        )
        is pipedrive_handler
    )


def test_provider_registers_xero_handler():
    registry = CustomerReconciliationHandlerRegistry()

    pipedrive_handler = MagicMock()
    xero_handler = MagicMock()

    provider = CustomerReconciliationHandlerProvider(
        registry=registry,
        pipedrive_handler=pipedrive_handler,
        xero_handler=xero_handler,
    )

    provider.register_defaults()

    assert (
        registry.get(
            source="xero",
            entity_type="contact",
        )
        is xero_handler
    )


def test_provider_registers_only_supported_defaults():
    registry = CustomerReconciliationHandlerRegistry()

    provider = CustomerReconciliationHandlerProvider(
        registry=registry,
        pipedrive_handler=MagicMock(),
        xero_handler=MagicMock(),
    )

    provider.register_defaults()

    assert registry.keys() == [
        ("pipedrive", "organization"),
        ("xero", "contact"),
    ]
