from apps.ai.prompts.deal_risk import (
    DEAL_RISK_PROMPT_VERSION,
    SYSTEM_PROMPT,
    build_deal_risk_prompt,
)


def test_deal_risk_prompt_has_version():
    assert DEAL_RISK_PROMPT_VERSION == "deal_risk_v2"


def test_deal_risk_prompt_rejects_empty_evidence():
    try:
        build_deal_risk_prompt({})
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError for empty evidence"
    )


def test_deal_risk_prompt_contains_evidence():
    evidence = {
        "deal": {
            "id": 456,
            "title": "Acme H100 Expansion",
        },
        "crm": {
            "economic_buyer_engaged": False,
            "internal_build_project": True,
        },
    }

    prompt = build_deal_risk_prompt(evidence)

    assert "Acme H100 Expansion" in prompt
    assert "economic_buyer_engaged" in prompt
    assert "internal_build_project" in prompt
    assert "recommended_action" in prompt