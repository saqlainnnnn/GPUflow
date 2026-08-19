from unittest.mock import MagicMock, patch

from apps.gpuaas.app.services.customer_reconciliation_factory import (
    CustomerReconciliationFactory,
)


def test_factory_builds_registry_with_supported_handlers():
    session = MagicMock()

    pipedrive_client = MagicMock()

    with patch(
        "apps.gpuaas.app.services."
        "customer_reconciliation_factory."
        "get_pipedrive_client",
        return_value=pipedrive_client,
    ):
        factory = CustomerReconciliationFactory(
            session=session,
        )

        registry = factory.build_registry()

    assert registry.get(
        source="pipedrive",
        entity_type="organization",
    ) is not None

    assert registry.get(
        source="xero",
        entity_type="contact",
    ) is not None


def test_factory_builds_job():
    session = MagicMock()

    with patch(
        "apps.gpuaas.app.services."
        "customer_reconciliation_factory."
        "get_pipedrive_client",
        return_value=MagicMock(),
    ):
        factory = CustomerReconciliationFactory(
            session=session,
        )

        job = factory.build_job()

    assert job is not None


def test_factory_registers_pipedrive_and_xero_handlers():
    from apps.gpuaas.app.services.pipedrive_customer_reconciliation_handler import (
        PipedriveCustomerReconciliationHandler,
    )
    from apps.gpuaas.app.services.xero_customer_reconciliation_handler import (
        XeroCustomerReconciliationHandler,
    )

    session = MagicMock()

    with patch(
        "apps.gpuaas.app.services."
        "customer_reconciliation_factory."
        "get_pipedrive_client",
        return_value=MagicMock(),
    ):
        factory = CustomerReconciliationFactory(
            session=session,
        )

        registry = factory.build_registry()

    pipedrive_handler = registry.get(
        source="pipedrive",
        entity_type="organization",
    )

    xero_handler = registry.get(
        source="xero",
        entity_type="contact",
    )

    assert isinstance(
        pipedrive_handler,
        PipedriveCustomerReconciliationHandler,
    )

    assert isinstance(
        xero_handler,
        XeroCustomerReconciliationHandler,
    )
