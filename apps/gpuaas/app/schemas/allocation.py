from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AllocationCreate(BaseModel):
    customer_id: UUID
    gpu_type: str = Field(min_length=1, max_length=50)
    gpu_count: int = Field(gt=0)
    region: str = Field(min_length=1, max_length=50)


class AllocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    gpu_type: str
    gpu_count: int
    region: str
    status: str
