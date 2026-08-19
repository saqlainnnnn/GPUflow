from uuid import uuid4

from sqlalchemy import inspect

from apps.gpuaas.app.models.customer_reconciliation_run import (
    CustomerReconciliationRun,
)


def test_run_has_expected_fields():
    columns = inspect(CustomerReconciliationRun).columns

    assert "id" in columns
    assert "status" in columns
    assert "started_at" in columns
    assert "completed_at" in columns
    assert "processed" in columns
    assert "succeeded" in columns
    assert "failed" in columns


def test_run_can_be_created():
    run = CustomerReconciliationRun(
        status="running",
        processed=0,
        succeeded=0,
        failed=0,
    )

    assert run.status == "running"
    assert run.processed == 0
    assert run.succeeded == 0
    assert run.failed == 0
