from typing import Any


class CustomerReconciliationHandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[
            tuple[str, str],
            Any,
        ] = {}

    def register(
        self,
        *,
        source: str,
        entity_type: str,
        handler: Any,
    ) -> None:
        self._handlers[
            (source, entity_type)
        ] = handler

    def get(
        self,
        *,
        source: str,
        entity_type: str,
    ) -> Any | None:
        return self._handlers.get(
            (source, entity_type)
        )

    def keys(self) -> list[tuple[str, str]]:
        return list(self._handlers.keys())
