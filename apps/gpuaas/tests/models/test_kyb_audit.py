from sqlalchemy import inspect

from apps.gpuaas.app.models.kyb_audit import KYBAudit


def test_kyb_audit_has_expected_fields():
    columns = inspect(KYBAudit).columns

    assert "id" in columns
    assert "customer_id" in columns
    assert "check_type" in columns
    assert "input_snapshot" in columns
    assert "decision" in columns
    assert "reason" in columns
    assert "timestamp" in columns
    assert "reviewer" in columns
