from dataclasses import dataclass


@dataclass(frozen=True)
class DuplicateCandidate:
    left_id: str
    right_id: str
    match_reasons: list[str]


class CustomerDuplicateDetectionService:
    def find_candidates(
        self,
        records: list[dict],
    ) -> list[DuplicateCandidate]:
        candidates: list[DuplicateCandidate] = []

        for index, left in enumerate(records):
            for right in records[index + 1:]:
                left_id = str(left["id"])
                right_id = str(right["id"])

                if left_id == right_id:
                    continue

                reasons: list[str] = []

                left_email = self._normalize_email(
                    left.get("email")
                )
                right_email = self._normalize_email(
                    right.get("email")
                )

                if (
                    left_email is not None
                    and right_email is not None
                    and left_email == right_email
                ):
                    reasons.append("email")

                left_company = self._normalize_company(
                    left.get("company_name")
                )
                right_company = self._normalize_company(
                    right.get("company_name")
                )

                if (
                    left_company is not None
                    and right_company is not None
                    and left_company == right_company
                ):
                    reasons.append("company_name")

                if reasons:
                    candidates.append(
                        DuplicateCandidate(
                            left_id=left_id,
                            right_id=right_id,
                            match_reasons=reasons,
                        )
                    )

        return candidates

    @staticmethod
    def _normalize_email(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip().lower()

        return normalized or None

    @staticmethod
    def _normalize_company(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = " ".join(
            value.strip().split()
        ).lower()

        return normalized or None
