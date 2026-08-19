from typing import Literal

from pydantic import BaseModel, Field


class KYBReviewRequest(BaseModel):
    decision: Literal["approve", "reject"]
    reviewer: str = Field(
        min_length=1,
        max_length=255,
    )
