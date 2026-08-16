from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DealRiskEvalExpected(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_level: str
    score_min: int = Field(ge=0, le=100)
    score_max: int = Field(ge=0, le=100)
    recommended_action: str


class DealRiskEvalCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    description: str
    category: str
    evidence: dict[str, Any]
    expected: DealRiskEvalExpected
    required_signals: list[str]
    forbidden_conclusions: list[str]
