from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.services.customer_field_ownership import (
    CustomerFieldOwnershipPolicy,
)
from apps.gpuaas.app.services.customer_reconciliation import (
    CustomerSourceReconciliation,
    CustomerReconciliationStatus,
    FieldReconciliation,
    FieldReconciliationStatus,
)
from apps.gpuaas.app.services.customer_reconciliation_runner import (
    CustomerReconciliationRunner,
)


def build_runner():
    reconciler = AsyncMock()
    persistence = AsyncMock()

    runner = CustomerReconciliationRunner(
        reconciler=reconciler,
        persistence=persistence,
    )

    return runner, reconciler, persistence


def build_policy():
    return CustomerFieldOwnershipPolicy(
        {
            "company_name": "pipedrive",
            "email": "pipedrive",
            "country": "pipedrive",
        }
    )


@pytest.mark.asyncio
async def test_reconcile_and_persist_includes_ownership_classification():
    runner, reconciler, persistence = build_runner()

    customer_id = uuid4()

    reconciliation = CustomerSourceReconciliation(
        source="pipedrive",
        entity_type="organization",
        status=CustomerReconciliationStatus.MISMATCH,
        mismatches=["company_name"],
        missing=[],
        fields={
            "company_name": FieldReconciliation(
                field="company_name",
                status=FieldReconciliationStatus.MISMATCH,
                canonical_value="acme ai",
                source_value="acme compute",
            ),
        },
    )

    persisted = MagicMock()

    reconciler.reconcile_identity.return_value = reconciliation
    persistence.persist.return_value = persisted

    result, record = await runner.reconcile_and_persist(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        source_record={
            "company_name": "Acme Compute",
        },
        adapter=MagicMock(),
        ownership_policy=build_policy(),
    )

    assert result is reconciliation
    assert record is persisted

    persistence.persist.assert_awaited_once()

    persisted_reconciliation = (
        persistence.persist.await_args.kwargs[
            "reconciliation"
        ]
    )

    classified = (
        persisted_reconciliation.fields[
            "company_name"
        ]
    )

    assert classified.ownership.value == "authoritative"
    assert (
        classified.classification.value
        == "authoritative_mismatch"
    )


@pytest.mark.asyncio
async def test_reconcile_without_policy_preserves_original_fields():
    runner, reconciler, persistence = build_runner()

    customer_id = uuid4()

    original_field = FieldReconciliation(
        field="email",
        status=FieldReconciliationStatus.MATCH,
        canonical_value="a@x.com",
        source_value="a@x.com",
    )

    reconciliation = CustomerSourceReconciliation(
        source="pipedrive",
        entity_type="organization",
        status=CustomerReconciliationStatus.MATCHED,
        mismatches=[],
        missing=[],
        fields={
            "email": original_field,
        },
    )

    persistence.persist.return_value = MagicMock()
    reconciler.reconcile_identity.return_value = (
        reconciliation
    )

    await runner.reconcile_and_persist(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        source_record={},
        adapter=MagicMock(),
    )

    persisted_reconciliation = (
        persistence.persist.await_args.kwargs[
            "reconciliation"
        ]
    )

    assert (
        persisted_reconciliation.fields["email"]
        is original_field
    )


@pytest.mark.asyncio
async def test_reconcile_and_persist_resolves_mismatched_authoritative_field():
    runner, reconciler, persistence = build_runner()

    customer_id = uuid4()

    field = FieldReconciliation(
        field="company_name",
        status=FieldReconciliationStatus.MISMATCH,
        canonical_value="Acme AI",
        source_value="Acme Compute",
    )

    reconciliation = CustomerSourceReconciliation(
        source="pipedrive",
        entity_type="organization",
        status=CustomerReconciliationStatus.MISMATCH,
        mismatches=["company_name"],
        missing=[],
        fields={
            "company_name": field,
        },
    )

    reconciler.reconcile_identity.return_value = (
        reconciliation
    )

    conflict_resolution = AsyncMock()

    resolution = MagicMock()
    resolution.value = "Acme Compute"

    conflict_resolution.resolve.return_value = (
        resolution
    )

    persisted = MagicMock()
    persistence.persist.return_value = persisted

    runner = CustomerReconciliationRunner(
        reconciler=reconciler,
        persistence=persistence,
        conflict_resolution=conflict_resolution,
    )

    policy = build_policy()

    result, record = await runner.reconcile_and_persist(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        source_record={
            "company_name": "Acme Compute",
        },
        adapter=MagicMock(),
        ownership_policy=policy,
    )

    assert result is reconciliation
    assert record is persisted

    conflict_resolution.resolve.assert_awaited_once_with(
        customer_id=customer_id,
        source="pipedrive",
        entity_type="organization",
        external_id="12345",
        field="company_name",
        canonical_value="Acme AI",
        source_value="Acme Compute",
        policy=policy,
    )
