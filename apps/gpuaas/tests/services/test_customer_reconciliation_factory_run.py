from unittest.mock import MagicMock, patch

from apps.gpuaas.app.services.customer_reconciliation_factory import (
    CustomerReconciliationFactory,
)
from apps.gpuaas.app.services.customer_reconciliation_run_service import (
    CustomerReconciliationRunService,
)


def test_factory_builds_run_service():
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

        service = factory.build_run_service()

    assert isinstance(
        service,
        CustomerReconciliationRunService,
    )
