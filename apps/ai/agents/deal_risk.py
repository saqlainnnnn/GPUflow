import json
from datetime import date
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from apps.ai.core.llm import (
    LLMRequest,
    LLMService,
)
from apps.ai.deal_risk.action_policy import (
    derive_recommended_action,
)
from apps.ai.deal_risk.evidence import (
    DealRiskEvidenceCollector,
)
from apps.ai.deal_risk.risk_guardrails import (
    apply_risk_floor,
)
from apps.ai.deal_risk.schemas import (
    DealRiskLLMOutput,
    DealRiskLLMResult,
    DealRiskResult,
)
from apps.ai.deal_risk.scoring import (
    DealRiskScorer,
)
from apps.ai.deal_risk.signals import (
    DealRiskSignalEngine,
    DealRiskSignalInput,
)
from apps.ai.deal_risk.writeback import (
    DealRiskWriteback,
)
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

        deterministic_signals = self.signal_engine.evaluate(
            signal_input,
        )

        deterministic_score = self.scorer.score(
            deterministic_signals.signals,
        )

        deterministic_risk_level = getattr(
            deterministic_score.level,
            "value",
            deterministic_score.level,
        )

        prompt_evidence = {
            **evidence,
            "deterministic_signals": {
                "deal_age_days": (
                    deterministic_signals.deal_age_days
                ),
                "stage_age_days": (
                    deterministic_signals.stage_age_days
                ),
                "days_since_last_activity": (
                    deterministic_signals.days_since_last_activity
                ),
                "usage_declining": (
                    deterministic_signals.usage_declining
                ),
                "jobs_unhealthy": (
                    deterministic_signals.jobs_unhealthy
                ),
                "spend_declining": (
                    deterministic_signals.spend_declining
                ),
                "signals": deterministic_signals.signals,
            },
            "deterministic_risk_score": (
                deterministic_score.score
            ),
            "deterministic_risk_level": str(
                deterministic_risk_level
            ),
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

        llm_result = self._parse_llm_response(
            response.content,
        )

        canonical_signals = list(
            deterministic_signals.signals,
        )

        final_score, final_level = apply_risk_floor(
            risk_score=llm_result.risk_score,
            risk_level=llm_result.risk_level,
            signals=canonical_signals,
        )

        recommended_action = derive_recommended_action(
            risk_level=final_level,
            signals=canonical_signals,
        )

        # The returned result exposes the canonical deterministic
        # signals because those are the actual source of truth for
        # the business decision and evaluation.
        result = DealRiskResult(
            risk_score=final_score,
            risk_level=final_level,
            signals=[
                {
                    "name": signal,
                    "severity": "medium",
                    "evidence": signal.replace(
                        "_",
                        " ",
                    ),
                }
                for signal in canonical_signals
            ],
            questions_to_probe=(
                llm_result.questions_to_probe
            ),
            recommended_action=recommended_action,
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

        crm = evidence.get(
            "crm",
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
            technical_champion_engaged=crm.get(
                "technical_champion_engaged",
            ),
            economic_buyer_engaged=crm.get(
                "economic_buyer_engaged",
            ),
            internal_build_project=crm.get(
                "internal_build_project",
            ),
            facility_power_ready=crm.get(
                "facility_power_ready",
            ),
            sovereignty_required=crm.get(
                "sovereignty_required",
            ),
            eu_region_required=crm.get(
                "eu_region_required",
            ),
            air_gapped_requirement=crm.get(
                "air_gapped_requirement",
            ),
            price_sensitivity=crm.get(
                "price_sensitivity",
            ),
            roi_conversation_completed=crm.get(
                "roi_conversation_completed",
            ),
            top_customer_revenue_percent=crm.get(
                "top_customer_revenue_percent",
            ),
            cash_runway_months=crm.get(
                "cash_runway_months",
            ),
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
    def _parse_llm_response(
        content: str,
    ) -> DealRiskLLMResult:
        cleaned = content.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            if (
                lines
                and lines[0].strip().startswith("```")
            ):
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

            cleaned = "\n".join(
                lines,
            ).strip()

        try:
            payload = json.loads(
                cleaned,
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Deal risk LLM response was not valid JSON",
            ) from exc

        if not isinstance(payload, dict):
            raise ValueError(
                "Deal risk LLM response must be a JSON object",
            )

        payload = dict(payload)

        payload.pop(
            "recommended_action",
            None,
        )

        payload.pop(
            "determined_risk_score",
            None,
        )

        payload.pop(
            "determined_risk_level",
            None,
        )

        try:
            llm_output = DealRiskLLMOutput.model_validate(
                payload,
            )
        except ValidationError as exc:
            raise ValueError(
                "Deal risk LLM response did not match "
                "the expected schema: "
                f"{cleaned}",
            ) from exc

        return DealRiskLLMResult.from_llm_output(
            llm_output,
        )
