from typing import Any, Protocol

from apps.ai.deal_risk.schemas import DealRiskResult


class PipedriveDealClient(Protocol):
    async def update_deal(
        self,
        deal_id: int,
        *,
        fields: dict[str, Any],
    ) -> dict[str, Any]: ...


class DealRiskWriteback:
    def __init__(
        self,
        *,
        pipedrive_client: PipedriveDealClient,
        risk_score_field: str,
        risk_level_field: str,
        signals_field: str,
        recommendation_field: str,
    ) -> None:
        fields = {
            "risk_score_field": risk_score_field,
            "risk_level_field": risk_level_field,
            "signals_field": signals_field,
            "recommendation_field": recommendation_field,
        }

        for name, value in fields.items():
            if not value:
                raise ValueError(
                    f"{name} is required",
                )

        self.pipedrive_client = pipedrive_client
        self.risk_score_field = risk_score_field
        self.risk_level_field = risk_level_field
        self.signals_field = signals_field
        self.recommendation_field = recommendation_field

    async def write(
        self,
        *,
        deal_id: int,
        result: DealRiskResult,
    ) -> None:
        await self.pipedrive_client.update_deal(
            deal_id,
            fields={
                self.risk_score_field: result.risk_score,
                self.risk_level_field: result.risk_level,
                self.signals_field: ", ".join(result.signals),
                self.recommendation_field: result.recommended_action,
            },
        )
