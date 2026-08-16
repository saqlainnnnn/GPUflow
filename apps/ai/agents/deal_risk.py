import json
from datetime import date
from typing import Any
from uuid import UUID

from apps.ai.core.llm import LLMRequest, LLMService
from apps.ai.deal_risk.evidence import DealRiskEvidenceCollector
from apps.ai.deal_risk.schemas import DealRiskResult
from apps.ai.deal_risk.scoring import DealRiskScorer
from apps.ai.deal_risk.signals import (
    DealRiskSignalEngine,
    DealRiskSignalInput,
)
from apps.ai.deal_risk.writeback import DealRiskWriteback
from apps.ai.prompts.deal_risk import (
    DEAL_RISK_PROMPT_VERSION,
    SYSTEM_PROMPT,
    build_deal_risk_prompt,
)


class DealRiskAgent:
    def __init__(
        self,
        *,
        llm: LLMService,
        evidence_collector: DealRiskEvidenceCollector,
        signal_engine: DealRiskSignalEngine,
        scorer: DealRiskScorer,
        writeback: DealRiskWriteback | None = None,
    ) -> None:
        if evidence_collector is None:
            raise ValueError(
                "evidence_collector is required",
            )

        if signal_engine is None:
            raise ValueError(
                "signal_engine is required",
            )

        if scorer is None:
            raise ValueError(
                "scorer is required",
            )

        self.llm = llm
        self.evidence_collector = evidence_collector
        self.signal_engine = signal_engine
        self.scorer = scorer
        self.writeback = writeback

    async def analyze(
        self,
        *,
        deal_id: int,
        organization_id: int,
        customer_id: UUID,
        today: date,
        writeback: bool = False,
    ) -> DealRiskResult:
        evidence = await self.evidence_collector.collect(
            deal_id=deal_id,
            organization_id=organization_id,
            customer_id=customer_id,
            today=today,
        )

        if not evidence:
            raise ValueError(
                "Deal risk evidence cannot be empty",
            )

        signal_input = self._build_signal_input(
            evidence=evidence,
            today=today,
        )

        signals = self.signal_engine.evaluate(
            signal_input,
        )

        risk_score = self.scorer.score(
            signals.signals,
        )

        prompt_evidence = {
            **evidence,
            "deterministic_signals": {
                "deal_age_days": signals.deal_age_days,
                "stage_age_days": signals.stage_age_days,
                "days_since_last_activity": (
                    signals.days_since_last_activity
                ),
                "usage_declining": signals.usage_declining,
                "jobs_unhealthy": signals.jobs_unhealthy,
                "spend_declining": signals.spend_declining,
                "signals": signals.signals,
            },
            "deterministic_risk_score": risk_score.score,
            "deterministic_risk_level": risk_score.level,
        }

        prompt = build_deal_risk_prompt(
            evidence=prompt_evidence,
        )

        response = await self.llm.generate(
            LLMRequest(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                prompt_version=DEAL_RISK_PROMPT_VERSION,
            )
        )

        result = self._parse_response(
            response.content,
        )

        if writeback:
            if self.writeback is None:
                raise ValueError(
                    "writeback requested but no writeback service configured",
                )

            await self.writeback.write(
                deal_id=deal_id,
                result=result,
            )

        return result

    @staticmethod
    def _build_signal_input(
        *,
        evidence: dict[str, Any],
        today: date,
    ) -> DealRiskSignalInput:
        deal = evidence.get(
            "deal",
            {},
        )
        usage = evidence.get(
            "usage",
            {},
        )
        usage_summary = usage.get(
            "summary",
            {},
        )
        jobs = evidence.get(
            "jobs",
            {},
        )
        billing = evidence.get(
            "billing",
            {},
        )

        deal_created_at = DealRiskAgent._parse_date(
            deal.get("created_at"),
        )

        if deal_created_at is None:
            raise ValueError(
                "Deal evidence missing created_at",
            )

        stage_entered_at = DealRiskAgent._parse_date(
            evidence.get(
                "stage_entered_at",
            ),
        )

        last_activity_at = DealRiskAgent._parse_date(
            evidence.get(
                "last_activity_at",
            ),
        )

        return DealRiskSignalInput(
            deal_created_at=deal_created_at,
            stage_entered_at=stage_entered_at,
            last_activity_at=last_activity_at,
            usage_growth_7d_percent=usage_summary.get(
                "growth_7d_percent",
            ),
            usage_growth_30d_percent=usage_summary.get(
                "growth_30d_percent",
            ),
            failed_jobs_30d=jobs.get(
                "failed_jobs_30d",
            ),
            total_jobs_30d=jobs.get(
                "total_jobs_30d",
            ),
            spend_growth_30d_percent=billing.get(
                "spend_growth_30d_percent",
            ),
            today=today,
        )

    @staticmethod
    def _parse_date(
        value: Any,
    ) -> date | None:
        if value is None:
            return None

        if isinstance(value, date):
            return value

        if isinstance(value, str):
            return date.fromisoformat(
                value[:10],
            )

        raise ValueError(
            f"Unsupported date value: {value!r}",
        )

    @staticmethod
    def _parse_response(
        content: str,
    ) -> DealRiskResult:
        try:
            payload = json.loads(
                content,
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Deal risk LLM response was not valid JSON",
            ) from exc

        return DealRiskResult.model_validate(
            payload,
        )
