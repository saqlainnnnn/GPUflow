from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.services.customer_duplicate_scan import (
    CustomerDuplicateScanService,
)


def build_service():
    customer_repository = AsyncMock()
    detector = MagicMock()
    issue_service = AsyncMock()

    service = CustomerDuplicateScanService(
        customer_repository=customer_repository,
        detector=detector,
        issue_service=issue_service,
    )

    return (
        service,
        customer_repository,
        detector,
        issue_service,
    )


def build_candidate(left_id, right_id):
    candidate = MagicMock()
    candidate.left_id = str(left_id)
    candidate.right_id = str(right_id)
    candidate.match_reasons = ["email"]

    return candidate


def build_issue(left_id, right_id):
    issue = MagicMock()
    issue.issue_type = "duplicate_candidate"
    issue.source = "gpuflow"
    issue.entity_type = "customer"

    first, second = sorted(
        [str(left_id), str(right_id)]
    )

    issue.external_id = f"{first}:{second}"

    issue.customer_id = left_id
    issue.details = {
        "right_customer_id": str(right_id),
        "match_reasons": ["email"],
    }
    issue.status = "open"

    return issue


@pytest.mark.asyncio
async def test_scan_resolves_stale_duplicate_issue():
    (
        service,
        customer_repository,
        detector,
        issue_service,
    ) = build_service()

    customer_a = uuid4()
    customer_b = uuid4()

    customer_repository.list_customers.return_value = [
        MagicMock(
            id=customer_a,
            company_name="Acme AI",
            email="hello@acme.ai",
        ),
        MagicMock(
            id=customer_b,
            company_name="Beta Compute",
            email="beta@compute.ai",
        ),
    ]

    detector.find_candidates.return_value = []

    stale_issue = build_issue(
        customer_a,
        customer_b,
    )

    issue_service.list_open_duplicate_candidates = AsyncMock(
        return_value=[stale_issue]
    )

    issue_service.resolve_candidate.return_value = (
        stale_issue
    )

    result = await service.scan()

    assert result == []

    issue_service.resolve_candidate.assert_awaited_once()

    candidate = (
        issue_service.resolve_candidate.await_args.args[0]
    )

    assert candidate.left_id == str(customer_a)
    assert candidate.right_id == str(customer_b)


@pytest.mark.asyncio
async def test_scan_keeps_current_duplicate_issue_open():
    (
        service,
        customer_repository,
        detector,
        issue_service,
    ) = build_service()

    customer_a = uuid4()
    customer_b = uuid4()

    customer_repository.list_customers.return_value = [
        MagicMock(
            id=customer_a,
            company_name="Acme AI",
            email="hello@acme.ai",
        ),
        MagicMock(
            id=customer_b,
            company_name="Acme Compute",
            email="HELLO@ACME.AI",
        ),
    ]

    current_candidate = build_candidate(
        customer_a,
        customer_b,
    )

    detector.find_candidates.return_value = [
        current_candidate
    ]

    issue_service.open_candidate.return_value = (
        "issue-123"
    )

    issue_service.list_open_duplicate_candidates = AsyncMock(
        return_value=[
            build_issue(
                customer_a,
                customer_b,
            )
        ]
    )

    result = await service.scan()

    assert result == ["issue-123"]

    issue_service.open_candidate.assert_awaited_once_with(
        current_candidate
    )

    issue_service.resolve_candidate.assert_not_awaited()


@pytest.mark.asyncio
async def test_scan_resolves_only_stale_candidates():
    (
        service,
        customer_repository,
        detector,
        issue_service,
    ) = build_service()

    customer_a = uuid4()
    customer_b = uuid4()
    customer_c = uuid4()
    customer_d = uuid4()

    customer_repository.list_customers.return_value = [
        MagicMock(id=customer_a),
        MagicMock(id=customer_b),
        MagicMock(id=customer_c),
        MagicMock(id=customer_d),
    ]

    current_candidate = build_candidate(
        customer_a,
        customer_b,
    )

    stale_issue = build_issue(
        customer_c,
        customer_d,
    )

    detector.find_candidates.return_value = [
        current_candidate
    ]

    issue_service.list_open_duplicate_candidates = AsyncMock(
        return_value=[
            build_issue(
                customer_a,
                customer_b,
            ),
            stale_issue,
        ]
    )

    issue_service.open_candidate.return_value = (
        "current-issue"
    )

    result = await service.scan()

    assert result == ["current-issue"]

    issue_service.open_candidate.assert_awaited_once_with(
        current_candidate
    )

    issue_service.resolve_candidate.assert_awaited_once()

    resolved_candidate = (
        issue_service.resolve_candidate.await_args.args[0]
    )

    assert resolved_candidate.left_id == str(
        customer_c
    )
    assert resolved_candidate.right_id == str(
        customer_d
    )
