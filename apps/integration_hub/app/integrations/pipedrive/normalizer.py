from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid5

from apps.integration_hub.app.schemas.event import EventCreate

PIPEDRIVE_NAMESPACE = UUID("2a8e3f4b-1e4d-4e15-9bb1-f0e8ce7a0f91")


class PipedriveWebhookNormalizer:
    def normalize(
        self,
        payload: dict[str, Any],
    ) -> EventCreate:
        meta = payload.get("meta", {})
        data = payload.get("data", {})

        action = meta.get("action")
        object_type = meta.get("object")

        if not action:
            raise ValueError("Pipedrive webhook missing meta.action")

        if not object_type:
            raise ValueError("Pipedrive webhook missing meta.object")

        source_event_id = self._source_event_id(
            meta=meta,
            data=data,
        )

        occurred_at = self._occurred_at(meta)

        event_type = f"pipedrive.{object_type}.{action}"

        correlation_id = uuid5(
            PIPEDRIVE_NAMESPACE,
            source_event_id,
        )

        return EventCreate(
            event_type=event_type,
            source="pipedrive",
            source_event_id=source_event_id,
            occurred_at=occurred_at,
            correlation_id=correlation_id,
            payload={
                "meta": meta,
                "data": data,
            },
        )

    @staticmethod
    def _source_event_id(
        meta: dict[str, Any],
        data: dict[str, Any],
    ) -> str:
        webhook_id = meta.get("id")
        item_id = data.get("id")
        object_type = meta.get("object")
        action = meta.get("action")

        if webhook_id:
            return str(webhook_id)

        if item_id is None:
            raise ValueError("Pipedrive webhook does not contain meta.id or data.id")

        return f"{object_type}:{action}:{item_id}"

    @staticmethod
    def _occurred_at(
        meta: dict[str, Any],
    ) -> datetime:
        timestamp = meta.get("timestamp")

        if timestamp is None:
            return datetime.now(UTC)

        if isinstance(timestamp, str):
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(
                timestamp,
                tz=UTC,
            )

        raise ValueError("Unsupported Pipedrive webhook timestamp")
