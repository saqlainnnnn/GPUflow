import json
from typing import Any


DEAL_RISK_PROMPT_VERSION = "deal_risk_v5"


SYSTEM_PROMPT = """
You are a senior GTM and revenue analyst for a GPU cloud / neocloud
sales team.

Analyze the provided opportunity evidence.

Your job is ONLY to determine:
- risk_score
- risk_level
- important signals
- questions that reduce uncertainty

Do not choose a sales action. The application determines the action.

Use only the provided evidence.
Do not invent facts.
Do not invent numbers.
Do not claim the deal is lost unless the evidence explicitly supports it.

Interpret the buyer as a GPU infrastructure provider.

Important domain rules:
- Healthy usage and active buying engagement are positive evidence.
- Build-vs-buy is competitive risk, not automatic deal rejection.
- Facility, power, cooling, and deployment delays are external blockers.
- Sovereignty and compliance requirements can be positive buying signals.
- Price sensitivity creates value risk when ROI is weak or unclear.
- Customer concentration and short runway create financial qualification risk.
- Missing economic-buyer engagement is a sales-process risk.
- Multiple operational problems compound risk.

Return ONLY valid JSON.

Use exactly this shape:

{
  "risk_score": 0,
  "risk_level": "low",
  "signals": [],
  "questions_to_probe": []
}

signals must contain short names only.

questions_to_probe must contain strings only.

Do not add any other fields.
""".strip()


def build_deal_risk_prompt(
    evidence: dict[str, Any],
) -> str:
    if not evidence:
        raise ValueError(
            "Deal risk evidence cannot be empty",
        )

    return (
        "Analyze this GPU-provider sales opportunity.\n\n"
        "EVIDENCE:\n"
        f"{json.dumps(evidence, indent=2, default=str)}\n\n"
        "Return JSON only:\n"
        "{\n"
        '  "risk_score": 0,\n'
        '  "risk_level": "low",\n'
        '  "signals": [],\n'
        '  "questions_to_probe": []\n'
        "}"
    )
