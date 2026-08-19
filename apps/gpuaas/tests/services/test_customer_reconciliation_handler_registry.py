from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.services.customer_reconciliation_handler_registry import (
    CustomerReconciliationHandlerRegistry,
)


def build_registry():
    registry = CustomerReconciliationHandlerRegistry()
    return registry


@pytest.mark.asyncio
async def test_registered_handler_is_returned():
    registry = build_registry()

    handler = AsyncMock()

    registry.register(
        source="pipedrive",
        entity_type="organization",
        handler=handler,
    )

    result = registry.get(
        source="pipedrive",
        entity_type="organization",
    )

    assert result is handler


def test_missing_handler_returns_none():
    registry = build_registry()

    assert (
        registry.get(
            source="xero",
            entity_type="contact",
        )
        is None
    )


def test_registering_same_key_replaces_previous_handler():
    registry = build_registry()

    first = MagicMock()
    second = MagicMock()

    registry.register(
        source="pipedrive",
        entity_type="organization",
        handler=first,
    )

    registry.register(
        source="pipedrive",
        entity_type="organization",
        handler=second,
    )

    assert (
        registry.get(
            source="pipedrive",
            entity_type="organization",
        )
        is second
    )


def test_registry_contains_only_explicitly_registered_sources():
    registry = build_registry()

    registry.register(
        source="pipedrive",
        entity_type="organization",
        handler=MagicMock(),
    )

    assert registry.keys() == [
        ("pipedrive", "organization"),
    ]
