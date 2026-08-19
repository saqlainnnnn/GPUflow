from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class DealRiskSignal(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )

    name: str = Field(
        min_length=1,
    )
    severity: str = "medium"
    evidence: str = Field(
        min_length=1,
    )

    @field_validator(
        "severity",
        mode="before",
    )
    @classmethod
    def normalize_severity(
        cls,
        value: Any,
    ) -> str:
        if not isinstance(value, str):
            return "medium"

        normalized = value.strip().lower()

        if normalized in {
            "low",
            "medium",
            "high",
        }:
            return normalized

        return "medium"


class DealRiskQuestion(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )

    question: str = Field(
        min_length=1,
    )
    type: str = "open"

    @field_validator(
        "type",
        mode="before",
    )
    @classmethod
    def normalize_type(
        cls,
        value: Any,
    ) -> str:
        if not isinstance(value, str):
            return "open"

        normalized = value.strip().lower()

        if normalized in {
            "binary",
            "open",
        }:
            return normalized

        return "open"


class DealRiskLLMOutput(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )

    risk_score: int = Field(
        ge=0,
        le=100,
    )
    risk_level: str
    signals: list[Any] = Field(
        default_factory=list,
    )
    questions_to_probe: list[Any] = Field(
        default_factory=list,
    )

    @field_validator(
        "risk_score",
        mode="before",
    )
    @classmethod
    def normalize_score(
        cls,
        value: Any,
    ) -> int:
        try:
            score = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "risk_score must be numeric",
            ) from exc

        return max(
            0,
            min(
                100,
                score,
            ),
        )

    @field_validator(
        "risk_level",
        mode="before",
    )
    @classmethod
    def normalize_risk_level(
        cls,
        value: Any,
    ) -> str:
        if not isinstance(value, str):
            raise ValueError(
                "risk_level must be a string",
            )

        normalized = value.strip().lower()

        aliases = {
            "low": "low",
            "medium": "medium",
            "moderate": "medium",
            "mid": "medium",
            "med": "medium",
            "high": "high",
        }

        if normalized not in aliases:
            raise ValueError(
                f"Unsupported risk level: {value!r}",
            )

        return aliases[normalized]


class DealRiskLLMResult(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )

    risk_score: int = Field(
        ge=0,
        le=100,
    )
    risk_level: str
    signals: list[DealRiskSignal]
    questions_to_probe: list[DealRiskQuestion]

    @field_validator(
        "signals",
        mode="before",
    )
    @classmethod
    def normalize_signals(
        cls,
        value: Any,
    ) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            raise ValueError(
                "signals must be a list",
            )

        normalized: list[dict[str, Any]] = []

        for item in value:
            if isinstance(item, str):
                normalized.append(
                    {
                        "name": item,
                        "severity": "medium",
                        "evidence": item.replace(
                            "_",
                            " ",
                        ),
                    }
                )
                continue

            if not isinstance(item, dict):
                continue

            name = item.get("name")

            if not isinstance(name, str):
                continue

            evidence = item.get(
                "evidence",
            )

            # Some smaller models emit "question" alongside
            # the signal instead of a separate questions list.
            # Preserve the signal here; question extraction is
            # handled separately.
            if not isinstance(evidence, str):
                evidence = name.replace(
                    "_",
                    " ",
                )

            normalized.append(
                {
                    "name": name,
                    "severity": item.get(
                        "severity",
                        "medium",
                    ),
                    "evidence": evidence,
                }
            )

        return normalized

    @field_validator(
        "questions_to_probe",
        mode="before",
    )
    @classmethod
    def normalize_questions(
        cls,
        value: Any,
    ) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            raise ValueError(
                "questions_to_probe must be a list",
            )

        normalized: list[dict[str, Any]] = []

        for item in value:
            if isinstance(item, str):
                normalized.append(
                    {
                        "question": item,
                        "type": "open",
                    }
                )
                continue

            if not isinstance(item, dict):
                continue

            question = item.get(
                "question",
            )

            if isinstance(question, str):
                normalized.append(
                    {
                        "question": question,
                        "type": item.get(
                            "type",
                            "open",
                        ),
                    }
                )

        return normalized

    @classmethod
    def from_llm_output(
        cls,
        output: DealRiskLLMOutput,
    ) -> "DealRiskLLMResult":
        raw_signals = output.signals

        signal_models: list[DealRiskSignal] = []
        embedded_questions: list[DealRiskQuestion] = []

        for item in raw_signals:
            if isinstance(item, str):
                signal_models.append(
                    DealRiskSignal(
                        name=item,
                        severity="medium",
                        evidence=item.replace(
                            "_",
                            " ",
                        ),
                    )
                )
                continue

            if not isinstance(item, dict):
                continue

            name = item.get(
                "name",
            )

            if not isinstance(name, str):
                continue

            evidence = item.get(
                "evidence",
            )

            if not isinstance(evidence, str):
                evidence = name.replace(
                    "_",
                    " ",
                )

            signal_models.append(
                DealRiskSignal(
                    name=name,
                    severity=item.get(
                        "severity",
                        "medium",
                    ),
                    evidence=evidence,
                )
            )

            question = item.get(
                "question",
            )

            if isinstance(question, str):
                embedded_questions.append(
                    DealRiskQuestion(
                        question=question,
                        type="open",
                    )
                )

        questions = list(
            embedded_questions,
        )

        for item in output.questions_to_probe:
            if isinstance(item, str):
                questions.append(
                    DealRiskQuestion(
                        question=item,
                        type="open",
                    )
                )
            elif isinstance(item, dict):
                question = item.get(
                    "question",
                )

                if isinstance(question, str):
                    questions.append(
                        DealRiskQuestion(
                            question=question,
                            type=item.get(
                                "type",
                                "open",
                            ),
                        )
                    )

        return cls(
            risk_score=output.risk_score,
            risk_level=output.risk_level,
            signals=signal_models,
            questions_to_probe=questions,
        )


class DealRiskResult(DealRiskLLMResult):
    recommended_action: str = Field(
        min_length=1,
    )
