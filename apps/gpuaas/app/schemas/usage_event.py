from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UsageEventCreate(BaseModel):
    event_id: str = Field(min_length=1, max_length=100)
    customer_id: UUID
    allocation_id: UUID
    gpu_type: str = Field(min_length=1, max_length=50)
    gpu_hours: float = Field(gt=0)
    utilization: float = Field(ge=0, le=1)
    timestamp: datetime


class UsageEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_id: str
    customer_id: UUID
    allocation_id: UUID
    gpu_type: str
    gpu_hours: float
    utilization: float
    timestamp: datetime
