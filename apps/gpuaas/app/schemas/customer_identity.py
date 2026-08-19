from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CustomerIdentityCreate(BaseModel):
    source: str
    entity_type: str
    external_id: str


class CustomerIdentityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    source: str
    entity_type: str
    external_id: str
