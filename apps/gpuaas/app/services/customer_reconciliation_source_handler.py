from typing import Any


class CustomerReconciliationSourceHandler:
    def __init__(
        self,
        *,
        reconciler: Any,
    ) -> None:
        self.reconciler = reconciler

    async def reconcile(
        self,
        identity,
    ):
        return await self.reconciler(
            identity,
        )
