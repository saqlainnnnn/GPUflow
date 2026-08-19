from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.integration_hub.app.services.integration_health import (
    IntegrationHealthService,
)


def build_service():
    repository = AsyncMock()
    queue = AsyncMock()

    service = IntegrationHealthService(
        repository=repository,
        queue=queue,
    )

    return service, repository, queue


@pytest.mark.asyncio
async def test_health_returns_sync_sla_metrics():
    service, repository, queue = build_service()

    now = datetime.now(timezone.utc)

    oldest = MagicMock()
    oldest.occurred_at = now - timedelta(seconds=120)

    processed = MagicMock()
    processed.occurred_at = now - timedelta(seconds=30)
    processed.updated_at = now - timedelta(seconds=20)
    processed.retry_count = 0

    retrying = MagicMock()
    retrying.status = "retrying"
    retrying.retry_count = 2
    retrying.occurred_at = now - timedelta(seconds=10)

    repository.get_oldest_unprocessed.return_value = oldest
    repository.get_processed_events.return_value = [
        processed,
    ]
    repository.get_all_events.return_value = [
        processed,
        retrying,
    ]

    queue.dlq_size.return_value = 3

    snapshot = await service.get_health(now=now)

    assert snapshot.event_age_seconds == 120
    assert snapshot.delivery_latency_seconds == 10
    assert snapshot.failure_rate == 0.5
    assert snapshot.retry_depth == 1
    assert snapshot.dlq_depth == 3


@pytest.mark.asyncio
async def test_health_handles_no_events():
    service, repository, queue = build_service()

    now = datetime.now(timezone.utc)

    repository.get_oldest_unprocessed.return_value = None
    repository.get_processed_events.return_value = []
    repository.get_all_events.return_value = []

    queue.dlq_size.return_value = 0

    snapshot = await service.get_health(now=now)

    assert snapshot.event_age_seconds == 0
    assert snapshot.delivery_latency_seconds == 0
    assert snapshot.failure_rate == 0
    assert snapshot.retry_depth == 0
    assert snapshot.dlq_depth == 0
