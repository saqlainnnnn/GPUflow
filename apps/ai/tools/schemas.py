from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class GetCustomerInput(BaseModel):
    customer_id: UUID


class CreateCustomerInput(BaseModel):
    external_id: str = Field(
        min_length=1,
        max_length=100,
    )
    company_name: str = Field(
        min_length=1,
        max_length=255,
    )
    email: EmailStr
    country: str = Field(
        min_length=2,
        max_length=2,
    )
    status: str = Field(
        default="active",
        min_length=1,
        max_length=50,
    )


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
    created_at: str | None = None
    updated_at: str | None = None


class GetDealChangelogInput(BaseModel):
    deal_id: int


class DealChangelogToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_key: str
    old_value: int | str | None = None
    new_value: int | str | None = None
    timestamp: str


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
    updated_at: str | None = None


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


class GetJobsInput(BaseModel):
    customer_id: UUID


class JobToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    external_id: str
    customer_id: UUID
    allocation_id: UUID
    gpu_type: str
    gpu_count: int
    status: str
    duration_seconds: int
    failure_reason: str | None = None


class GetBillingInput(BaseModel):
    customer_id: UUID


class BillingLineItemToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usage_event_id: UUID
    timestamp: str | None = None
    gpu_type: str
    gpu_hours: float
    rate_per_gpu_hour: Decimal
    amount: Decimal


class BillingToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: UUID
    currency: str
    line_items: list[BillingLineItemToolOutput]
    total_gpu_hours: float
    subtotal: Decimal

class UpdateCustomerInput(BaseModel):
    customer_id: UUID
    company_name: str = Field(
        min_length=1,
        max_length=255,
    )
    email: EmailStr
    country: str = Field(
        min_length=2,
        max_length=2,
    )
    status: str = Field(
        min_length=1,
        max_length=50,
    )
    sync_origin: str = Field(
        default="gpuflow",
        max_length=50,
    )

class UpdatePipedriveOrganizationInput(BaseModel):
    organization_id: int
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    address: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
    )

    @model_validator(mode="after")
    def validate_update_fields(self):
        if self.name is None and self.address is None:
            raise ValueError(
                "At least one organization field must be provided"
            )

        return self

class PipedriveOrganizationToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    address: str | None = None
    owner_id: int | None = None