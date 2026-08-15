import pytest

from apps.ai.prompts.deal_risk import (
    DEAL_RISK_PROMPT_VERSION,
    build_deal_risk_prompt,
)


def test_deal_risk_prompt_has_version():
    assert DEAL_RISK_PROMPT_VERSION == "deal_risk_v1"


def test_build_deal_risk_prompt_contains_evidence():
    prompt = build_deal_risk_prompt(
        evidence={
            "deal_age_days": 76,
            "stage_age_days": 46,
            "days_since_last_activity": 15,
            "usage_growth_7d_percent": -35.0,
            "failed_jobs_30d": 8,
            "spend_growth_30d_percent": -30.0,
        }
    )

    assert "76" in prompt
    assert "46" in prompt
    assert "-35.0" in prompt
    assert "8" in prompt
    assert "-30.0" in prompt


def test_build_deal_risk_prompt_requires_evidence():
    with pytest.raises(ValueError):
        build_deal_risk_prompt(evidence={})
