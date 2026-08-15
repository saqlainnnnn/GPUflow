from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class RiskScore:
    score: int
    level: RiskLevel


class DealRiskScorer:
    SIGNAL_WEIGHTS: dict[str, int] = {
        "deal_stale": 20,
        "no_recent_activity": 20,
        "usage_declining": 25,
        "job_failures": 20,
        "spend_declining": 20,
    }

    MEDIUM_THRESHOLD = 40
    HIGH_THRESHOLD = 80

    def score(
        self,
        signals: list[str],
    ) -> RiskScore:
        score = sum(
            self.SIGNAL_WEIGHTS.get(signal, 0)
            for signal in set(signals)
        )

        score = min(score, 100)

        if score >= self.HIGH_THRESHOLD:
            level = RiskLevel.HIGH
        elif score >= self.MEDIUM_THRESHOLD:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        return RiskScore(
            score=score,
            level=level,
        )
