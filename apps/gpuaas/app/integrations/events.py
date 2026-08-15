from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


def build_customer_updated_event(
    customer_id: UUID,
    *,
    external_id: str,
    company_name: str,
    email: str,
    country: str,
    sync_origin: str,
) -> dict[str, Any]:
    return {
        "event_type": "customer.updated",
        "source": "gpuaas",
        "source_event_id": str(uuid4()),
        "occurred_at": datetime.now(UTC).isoformat(),
        "correlation_id": str(customer_id),
        "payload": {
            "customer_id": str(customer_id),
            "external_id": external_id,
            "company_name": company_name,
            "email": email,
            "country": country,
            "sync_origin": sync_origin,
        },
    }
