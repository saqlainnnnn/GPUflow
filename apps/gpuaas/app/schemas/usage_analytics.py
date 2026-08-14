from datetime import date
from uuid import UUID

from pydantic import BaseModel


class UsageSummaryResponse(BaseModel):
    customer_id: UUID
    total_gpu_hours: float
    average_utilization: float
    event_count: int
    gpu_hours_7d: float
    gpu_hours_30d: float
    growth_7d_percent: float | None
    growth_30d_percent: float | None


class GPUTypeUsage(BaseModel):
    gpu_type: str
    gpu_hours: float
    average_utilization: float


class DailyUsage(BaseModel):
    date: date
    gpu_hours: float
    average_utilization: float


class UsageAnalyticsResponse(BaseModel):
    customer_id: UUID
    summary: UsageSummaryResponse
    by_gpu_type: list[GPUTypeUsage]
    daily: list[DailyUsage]
