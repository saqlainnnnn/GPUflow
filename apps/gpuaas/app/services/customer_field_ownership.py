from enum import StrEnum


class OwnershipDecision(StrEnum):
    AUTHORITATIVE = "authoritative"
    NON_AUTHORITATIVE = "non_authoritative"
    UNKNOWN = "unknown"


class CustomerFieldOwnershipPolicy:
    def __init__(
        self,
        ownership: dict[str, str],
    ) -> None:
        self.ownership = dict(ownership)

    def authoritative_source(
        self,
        *,
        field: str,
    ) -> str | None:
        return self.ownership.get(field)

    def decide(
        self,
        *,
        field: str,
        source: str,
    ) -> OwnershipDecision:
        authoritative_source = (
            self.authoritative_source(field=field)
        )

        if authoritative_source is None:
            return OwnershipDecision.UNKNOWN

        if source == authoritative_source:
            return OwnershipDecision.AUTHORITATIVE

        return OwnershipDecision.NON_AUTHORITATIVE
