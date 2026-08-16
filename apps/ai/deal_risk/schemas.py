from pydantic import BaseModel, ConfigDict, Field


class DealRiskResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_score: int = Field(
        ge=0,
        le=100,
    )
    risk_level: str
    signals: list[str]
    questions_to_probe: list[str]
    recommended_action: str
