from pydantic import BaseModel


class IntegrationHealthResponse(BaseModel):
    event_age_seconds: int
    delivery_latency_seconds: float
    failure_rate: float
    retry_depth: float
    dlq_depth: int
