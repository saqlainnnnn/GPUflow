from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CustomerReconciliationRequest(BaseModel):
    source: str
    entity_type: str
    external_id: str
    source_record: dict[str, Any]


class CustomerReconciliationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: UUID
    source: str
    entity_type: str
    status: str
    mismatches: list[str]
    missing: list[str]
    fields: dict[str, dict[str, Any]]
