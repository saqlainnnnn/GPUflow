from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=100)
    source: str = Field(min_length=1, max_length=50)
    source_event_id: str = Field(min_length=1, max_length=255)
    occurred_at: datetime
    correlation_id: UUID
    payload: dict


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_id: UUID
    event_type: str
    source: str
    source_event_id: str
    occurred_at: datetime
    correlation_id: UUID
    status: str
    retry_count: int
    last_error: str | None
    payload: dict


class EventIngestResponse(BaseModel):
    event: EventResponse
    created: bool
