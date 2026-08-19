from dataclasses import dataclass
from datetime import datetime, timezone

from apps.integration_hub.app.repositories.event import EventRepository
from apps.integration_hub.app.services.queue import EventQueue


@dataclass(frozen=True)
class IntegrationHealthSnapshot:
    event_age_seconds: int
    delivery_latency_seconds: float
    failure_rate: float
    retry_depth: float
    dlq_depth: int


class IntegrationHealthService:
    def __init__(
        self,
        *,
        repository: EventRepository,
        queue: EventQueue,
    ) -> None:
        self.repository = repository
        self.queue = queue

    async def get_health(
        self,
        *,
        now: datetime | None = None,
    ) -> IntegrationHealthSnapshot:
        now = now or datetime.now(timezone.utc)

        oldest = await self.repository.get_oldest_unprocessed()
        processed_events = (
            await self.repository.get_processed_events()
        )
        all_events = await self.repository.get_all_events()

        if oldest is None:
            event_age_seconds = 0
        else:
            event_age_seconds = max(
                0,
                int(
                    (now - oldest.occurred_at).total_seconds()
                ),
            )

        if processed_events:
            latencies = [
                max(
                    0.0,
                    (
                        event.updated_at
                        - event.occurred_at
                    ).total_seconds(),
                )
                for event in processed_events
            ]

            delivery_latency_seconds = (
                sum(latencies) / len(latencies)
            )
        else:
            delivery_latency_seconds = 0.0

        if all_events:
            failed_events = sum(
                event.status in {"retrying", "dead_letter"}
                for event in all_events
            )

            failure_rate = failed_events / len(all_events)

            retry_depth = (
                sum(event.retry_count for event in all_events)
                / len(all_events)
            )
        else:
            failure_rate = 0.0
            retry_depth = 0.0

        dlq_depth = await self.queue.dlq_size()

        return IntegrationHealthSnapshot(
            event_age_seconds=event_age_seconds,
            delivery_latency_seconds=delivery_latency_seconds,
            failure_rate=failure_rate,
            retry_depth=retry_depth,
            dlq_depth=dlq_depth,
        )
