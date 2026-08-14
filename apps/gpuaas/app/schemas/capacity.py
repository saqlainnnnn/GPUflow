from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CapacityCreate(BaseModel):
    region: str = Field(min_length=1, max_length=50)
    gpu_type: str = Field(min_length=1, max_length=50)
    total_gpus: int = Field(gt=0)


class CapacityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    region: str
    gpu_type: str
    total_gpus: int
    allocated_gpus: int
    status: str

    @property
    def available_gpus(self) -> int:
        return self.total_gpus - self.allocated_gpus
