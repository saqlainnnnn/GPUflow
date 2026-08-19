from dataclasses import dataclass
from enum import StrEnum
from difflib import SequenceMatcher


class KYBDecision(StrEnum):
    CLEAR = "clear"
    FLAGGED = "flagged"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class KYBCheck:
    check_type: str
    reason: str
    matched_value: str | None = None


@dataclass(frozen=True)
class KYBScreeningResult:
    decision: KYBDecision
    checks: list[KYBCheck]


RESTRICTED_COUNTRIES = {
    "XX",
    "YY",
}

DENIED_PARTIES = {
    "Example Restricted Corp",
    "Blocked Compute Ltd",
}

FUZZY_MATCH_THRESHOLD = 0.88


def _normalize(value: str) -> str:
    return " ".join(
        value.strip().lower().split()
    )


class KYBScreeningService:
    def screen_customer(
        self,
        *,
        company_name: str,
        country: str,
    ) -> KYBScreeningResult:
        checks: list[KYBCheck] = []

        normalized_country = country.strip().upper()
        normalized_company = _normalize(company_name)

        if normalized_country in RESTRICTED_COUNTRIES:
            checks.append(
                KYBCheck(
                    check_type="restricted_country",
                    reason=(
                        "Customer country matched the "
                        "restricted-country list."
                    ),
                    matched_value=normalized_country,
                )
            )

        denied_match = self._find_denied_party_match(
            normalized_company
        )

        if denied_match is not None:
            checks.append(
                KYBCheck(
                    check_type="denied_party",
                    reason=(
                        "Company name matched the "
                        "demo denied-party list."
                    ),
                    matched_value=denied_match,
                )
            )

        if any(
            check.check_type == "restricted_country"
            for check in checks
        ):
            decision = KYBDecision.BLOCKED
        elif any(
            check.check_type == "denied_party"
            for check in checks
        ):
            decision = KYBDecision.FLAGGED
        else:
            decision = KYBDecision.CLEAR

        return KYBScreeningResult(
            decision=decision,
            checks=checks,
        )

    def _find_denied_party_match(
        self,
        normalized_company: str,
    ) -> str | None:
        for denied_party in DENIED_PARTIES:
            normalized_denied = _normalize(
                denied_party
            )

            if normalized_company == normalized_denied:
                return denied_party

            ratio = SequenceMatcher(
                None,
                normalized_company,
                normalized_denied,
            ).ratio()

            if ratio >= FUZZY_MATCH_THRESHOLD:
                return denied_party

        return None
