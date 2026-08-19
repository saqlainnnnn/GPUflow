from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from apps.gpuaas.app.models.customer_data_quality_issue import (
    CustomerDataQualityIssue,
)
from apps.gpuaas.app.services.customer_duplicate_issue import (
    CustomerDuplicateIssueService,
)


def build_service():
    repository = AsyncMock()

    service = CustomerDuplicateIssueService(
        repository=repository,
    )

    return service, repository


def build_candidate(
    left_id=None,
    right_id=None,
    reasons=None,
):
    candidate = type("DuplicateCandidate", (), {})()

    candidate.left_id = str(left_id or uuid4())
    candidate.right_id = str(right_id or uuid4())
    candidate.match_reasons = reasons or ["email"]

    return candidate


@pytest.mark.asyncio
async def test_open_duplicate_candidate_creates_issue():
    service, repository = build_service()

    left_id = uuid4()
    right_id = uuid4()

    candidate = build_candidate(
        left_id=left_id,
        right_id=right_id,
    )

    first_id, second_id = sorted(
        [str(left_id), str(right_id)]
    )

    repository.find_by_identity.return_value = None

    created = CustomerDataQualityIssue(
        customer_id=left_id,
        issue_type="duplicate_candidate",
        source="gpuflow",
        entity_type="customer",
        external_id=f"{first_id}:{second_id}",
        status="open",
        details={
            "right_customer_id": second_id,
            "match_reasons": ["email"],
        },
    )

    repository.create.return_value = created

    result = await service.open_candidate(candidate)

    assert result is created

    repository.find_by_identity.assert_awaited_once_with(
        issue_type="duplicate_candidate",
        source="gpuflow",
        entity_type="customer",
        external_id=f"{first_id}:{second_id}",
    )

    repository.create.assert_awaited_once()

    issue = repository.create.await_args.args[0]

    assert issue.issue_type == "duplicate_candidate"
    assert issue.source == "gpuflow"
    assert issue.entity_type == "customer"
    assert issue.external_id == f"{first_id}:{second_id}"
    assert issue.customer_id == left_id
    assert issue.details["right_customer_id"] == str(right_id)
    assert issue.details["match_reasons"] == ["email"]


@pytest.mark.asyncio
async def test_open_duplicate_candidate_is_idempotent():
    service, repository = build_service()

    left_id = uuid4()
    right_id = uuid4()

    first_id, second_id = sorted(
        [str(left_id), str(right_id)]
    )

    existing = CustomerDataQualityIssue(
        customer_id=left_id,
        issue_type="duplicate_candidate",
        source="gpuflow",
        entity_type="customer",
        external_id=f"{first_id}:{second_id}",
        status="open",
        details={
            "right_customer_id": str(right_id),
            "match_reasons": ["email"],
        },
    )

    repository.find_by_identity.return_value = existing

    result = await service.open_candidate(
        build_candidate(
            left_id=left_id,
            right_id=right_id,
        )
    )

    assert result is existing
    repository.create.assert_not_awaited()
    repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_open_duplicate_candidate_updates_match_reasons():
    service, repository = build_service()

    left_id = uuid4()
    right_id = uuid4()

    first_id, second_id = sorted(
        [str(left_id), str(right_id)]
    )

    existing = CustomerDataQualityIssue(
        customer_id=left_id,
        issue_type="duplicate_candidate",
        source="gpuflow",
        entity_type="customer",
        external_id=f"{first_id}:{second_id}",
        status="open",
        details={
            "right_customer_id": second_id,
            "match_reasons": ["email"],
        },
    )

    repository.find_by_identity.return_value = existing
    repository.update.return_value = existing

    candidate = build_candidate(
        left_id=left_id,
        right_id=right_id,
        reasons=["email", "company_name"],
    )

    result = await service.open_candidate(candidate)

    assert result is existing

    assert existing.details["match_reasons"] == [
        "email",
        "company_name",
    ]

    repository.update.assert_awaited_once_with(existing)


@pytest.mark.asyncio
async def test_resolve_duplicate_candidate():
    service, repository = build_service()

    left_id = uuid4()
    right_id = uuid4()

    first_id, second_id = sorted(
        [str(left_id), str(right_id)]
    )

    existing = CustomerDataQualityIssue(
        customer_id=left_id,
        issue_type="duplicate_candidate",
        source="gpuflow",
        entity_type="customer",
        external_id=f"{first_id}:{second_id}",
        status="open",
        details={
            "right_customer_id": second_id,
            "match_reasons": ["email"],
        },
    )

    repository.find_by_identity.return_value = existing
    repository.update.return_value = existing

    result = await service.resolve_candidate(
        build_candidate(
            left_id=left_id,
            right_id=right_id,
        )
    )

    assert result is existing
    assert existing.status == "resolved"
    assert existing.resolved_at is not None

    repository.update.assert_awaited_once_with(existing)


@pytest.mark.asyncio
async def test_resolve_missing_candidate_returns_none():
    service, repository = build_service()

    repository.find_by_identity.return_value = None

    result = await service.resolve_candidate(
        build_candidate()
    )

    assert result is None
    repository.update.assert_not_awaited()
