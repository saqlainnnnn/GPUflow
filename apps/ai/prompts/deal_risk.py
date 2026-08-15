import json
from typing import Any

DEAL_RISK_PROMPT_VERSION = "deal_risk_v1"


SYSTEM_PROMPT = """
You are a B2B GPU cloud sales analyst.

Analyze the provided deal evidence and assess deal risk.

Rules:
- Use only the evidence provided.
- Do not invent facts.
- Distinguish observed evidence from inference.
- Identify the strongest risk signals.
- Recommend a concrete sales action.
- Return valid JSON matching the requested schema.
""".strip()


def build_deal_risk_prompt(
    evidence: dict[str, Any],
) -> str:
    if not evidence:
        raise ValueError("Deal risk evidence cannot be empty")

    return (
        "Analyze this deal using the following deterministic evidence:\n\n"
        f"{json.dumps(evidence, indent=2, default=str)}\n\n"
        "Return JSON with this structure:\n"
        "{\n"
        '  "risk_score": 0,\n'
        '  "risk_level": "low",\n'
        '  "signals": [],\n'
        '  "questions_to_probe": [],\n'
        '  "recommended_action": ""\n'
        "}"
    )
