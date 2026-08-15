import asyncio
import logging

from apps.gpuaas.app.db.session import AsyncSessionLocal
from apps.gpuaas.app.integrations.publisher import (
    get_integration_hub_publisher,
)
from apps.gpuaas.app.repositories.outbox import OutboxRepository

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 2
BATCH_SIZE = 25


async def process_outbox() -> int:
    async with AsyncSessionLocal() as session:
        repository = OutboxRepository(session)
        publisher = get_integration_hub_publisher()

        events = await repository.get_pending(limit=BATCH_SIZE)

        processed = 0

        for event in events:
            try:
                await publisher.publish(event.payload)

                await repository.mark_processed(event)
                processed += 1

                logger.info(
                    "Published outbox event %s",
                    event.id,
                )

            except Exception as exc:
                logger.exception(
                    "Failed to publish outbox event %s",
                    event.id,
                )

                await repository.mark_failed(
                    event,
                    error=str(exc),
                )

        await session.commit()

        return processed


async def worker_loop() -> None:
    logger.info("GPUFlow outbox worker started")

    while True:
        try:
            processed = await process_outbox()

            if processed:
                logger.info(
                    "Processed %s outbox events",
                    processed,
                )

        except Exception:
            logger.exception("Outbox worker failure")

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(worker_loop())
