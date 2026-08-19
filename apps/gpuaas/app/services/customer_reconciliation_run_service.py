from datetime import datetime, timezone
from typing import Any

from apps.gpuaas.app.models.customer_reconciliation_run import (
    CustomerReconciliationRun,
)
from apps.gpuaas.app.repositories.customer_reconciliation_run import (
    CustomerReconciliationRunRepository,
)


class CustomerReconciliationRunService:
    def __init__(
        self,
        *,
        repository: CustomerReconciliationRunRepository,
        job: Any,
    ) -> None:
        self.repository = repository
        self.job = job

    async def run(
        self,
    ) -> CustomerReconciliationRun:
        run = CustomerReconciliationRun(
            status="running",
            started_at=datetime.now(timezone.utc),
            processed=0,
            succeeded=0,
            failed=0,
        )

        await self.repository.create(run)

        try:
            result = await self.job.run()

        except Exception:
            run.status = "failed"
            run.completed_at = datetime.now(
                timezone.utc
            )

            await self.repository.update(run)

            raise

        run.status = "completed"
        run.processed = result["processed"]
        run.succeeded = result["succeeded"]
        run.failed = result["failed"]
        run.completed_at = datetime.now(
            timezone.utc
        )

        return await self.repository.update(run)
