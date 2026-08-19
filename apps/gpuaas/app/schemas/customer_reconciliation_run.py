from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CustomerReconciliationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    started_at: datetime
    completed_at: datetime | None
    processed: int
    succeeded: int
    failed: int
