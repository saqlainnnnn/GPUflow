from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class GetCustomerInput(BaseModel):
    customer_id: UUID


class CustomerToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    external_id: str
    company_name: str
    email: EmailStr
    country: str
    status: str


class GetOrganizationInput(BaseModel):
    organization_id: int


class OrganizationToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    address: str | None = None
    owner_id: int | None = None


class GetDealInput(BaseModel):
    deal_id: int


class DealToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    title: str
    value: float | int | None = None
    currency: str | None = None
    status: str
    stage_id: int | None = None
    organization_id: int | None = None
    owner_id: int | None = None


class GetActivitiesInput(BaseModel):
    deal_id: int


class ActivityToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activity_id: int
    subject: str
    type: str
    status: str
    due_date: str | None = None
    done: bool | None = None
    owner_id: int | None = None
    deal_id: int | None = None
    organization_id: int | None = None
    person_id: int | None = None


class GetUsageInput(BaseModel):
    customer_id: UUID


class UsageSummaryToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_gpu_hours: float
    average_utilization: float
    event_count: int
    gpu_hours_7d: float
    gpu_hours_30d: float
    growth_7d_percent: float | None
    growth_30d_percent: float | None


class GPUTypeUsageToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gpu_type: str
    gpu_hours: float
    average_utilization: float


class DailyUsageToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    gpu_hours: float
    average_utilization: float


class UsageToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: UUID
    summary: UsageSummaryToolOutput
    by_gpu_type: list[GPUTypeUsageToolOutput]
    daily: list[DailyUsageToolOutput]


class GetAllocationsInput(BaseModel):
    customer_id: UUID


class AllocationToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    customer_id: UUID
    gpu_type: str
    gpu_count: int
    region: str
    status: str
