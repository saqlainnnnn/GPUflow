from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.services.customer_duplicate_scan import (
    CustomerDuplicateScanService,
)


def build_service():
    detector = MagicMock()
    issue_service = AsyncMock()
    customer_repository = AsyncMock()

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


def candidate(left_id, right_id, reasons=None):
    result = MagicMock()
    result.left_id = str(left_id)
    result.right_id = str(right_id)
    result.match_reasons = reasons or ["email"]

    return result


@pytest.mark.asyncio
async def test_scan_opens_detected_duplicate_candidates():
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

    detector.find_candidates.return_value = [
        candidate(customer_a, customer_b),
    ]

    issue_service.open_candidate.return_value = (
        "issue-123"
    )

    result = await service.scan()

    assert result == ["issue-123"]

    customer_repository.list_customers.assert_awaited_once()
    detector.find_candidates.assert_called_once()

    issue_service.open_candidate.assert_awaited_once_with(
        detector.find_candidates.return_value[0]
    )


@pytest.mark.asyncio
async def test_scan_returns_empty_when_no_candidates():
    (
        service,
        customer_repository,
        detector,
        issue_service,
    ) = build_service()

    customer_repository.list_customers.return_value = []

    detector.find_candidates.return_value = []

    result = await service.scan()

    assert result == []

    issue_service.open_candidate.assert_not_awaited()
    issue_service.resolve_candidate.assert_not_awaited()


@pytest.mark.asyncio
async def test_scan_does_not_create_duplicate_issues_for_detector_output():
    (
        service,
        customer_repository,
        detector,
        issue_service,
    ) = build_service()

    customer_a = uuid4()
    customer_b = uuid4()

    duplicate = candidate(
        customer_a,
        customer_b,
        reasons=["email"],
    )

    customer_repository.list_customers.return_value = [
        MagicMock(
            id=customer_a,
            company_name="Acme AI",
            email="hello@acme.ai",
        ),
        MagicMock(
            id=customer_b,
            company_name="Acme AI",
            email="HELLO@ACME.AI",
        ),
    ]

    detector.find_candidates.return_value = [
        duplicate,
        duplicate,
    ]

    issue_service.open_candidate.return_value = (
        "issue-123"
    )

    result = await service.scan()

    assert result == ["issue-123"]

    issue_service.open_candidate.assert_awaited_once_with(
        duplicate
    )
