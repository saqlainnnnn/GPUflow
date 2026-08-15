from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerCreate(BaseModel):
    external_id: str = Field(min_length=1, max_length=100)
    company_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    country: str = Field(min_length=2, max_length=2)
    status: str = Field(default="active", min_length=1, max_length=50)


class CustomerUpdate(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    country: str = Field(min_length=2, max_length=2)
    status: str = Field(min_length=1, max_length=50)
    sync_origin: str = Field(default="gpuaas", max_length=50)


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_id: str
    company_name: str
    email: EmailStr
    country: str
    status: str
