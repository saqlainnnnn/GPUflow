import json
from uuid import UUID

from redis.asyncio import Redis

QUEUE_NAME = "gpuflow:integration-events"
DLQ_NAME = "gpuflow:integration-events:dlq"


class EventQueue:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def enqueue(self, event_id: UUID) -> None:
        await self.redis.rpush(
            QUEUE_NAME,
            json.dumps({"event_id": str(event_id)}),
        )

    async def enqueue_retry(
        self,
        event_id: UUID,
        retry_count: int,
    ) -> None:
        await self.redis.rpush(
            QUEUE_NAME,
            json.dumps(
                {
                    "event_id": str(event_id),
                    "retry_count": retry_count,
                }
            ),
        )

    async def enqueue_dlq(
        self,
        event_id: UUID,
        reason: str,
    ) -> None:
        await self.redis.rpush(
            DLQ_NAME,
            json.dumps(
                {
                    "event_id": str(event_id),
                    "reason": reason,
                }
            ),
        )

    async def dequeue(self) -> UUID:
        _, payload = await self.redis.blpop(QUEUE_NAME)

        data = json.loads(payload)

        return UUID(data["event_id"])

    async def dlq_size(self) -> int:
        return await self.redis.llen(DLQ_NAME)

    async def remove_from_dlq(self, event_id: UUID) -> None:
        matches = await self.redis.lrange(DLQ_NAME, 0, -1)

        for raw in matches:
            data = json.loads(raw)

            if data.get("event_id") == str(event_id):
                await self.redis.lrem(DLQ_NAME, 1, raw)
                return
