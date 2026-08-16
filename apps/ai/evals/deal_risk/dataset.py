import json
from datetime import date
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from apps.ai.evals.deal_risk.cases import DealRiskEvalCase


class DealRiskEvalRunnerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    deal_id: int
    organization_id: int
    customer_id: UUID
    today: date


class DealRiskEvalDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runner_config: DealRiskEvalRunnerConfig
    cases: list[DealRiskEvalCase]


def load_deal_risk_dataset(
    path: Path,
) -> list[DealRiskEvalCase]:
    return load_deal_risk_eval_dataset(path).cases


def load_deal_risk_eval_dataset(
    path: Path,
) -> DealRiskEvalDataset:
    payload = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(payload, dict):
        raise ValueError(
            "Deal Risk evaluation dataset must contain a JSON object",
        )

    return DealRiskEvalDataset.model_validate(
        payload,
    )
