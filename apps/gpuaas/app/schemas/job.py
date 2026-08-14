from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    external_id: str = Field(min_length=1, max_length=100)
    customer_id: UUID
    allocation_id: UUID
    gpu_count: int = Field(gt=0)
    status: str = Field(default="pending", max_length=50)


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_id: str
    customer_id: UUID
    allocation_id: UUID
    gpu_type: str
    gpu_count: int
    status: str
    duration_seconds: int
    failure_reason: str | None
