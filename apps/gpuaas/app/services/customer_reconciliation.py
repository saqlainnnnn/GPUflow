from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class FieldReconciliationStatus(StrEnum):
    MATCH = "match"
    MISMATCH = "mismatch"
    MISSING_ON_SOURCE = "missing_on_source"
    MISSING_ON_CANONICAL = "missing_on_canonical"


class CustomerReconciliationStatus(StrEnum):
    MATCHED = "matched"
    INCOMPLETE = "incomplete"
    MISMATCH = "mismatch"


@dataclass(frozen=True)
class NormalizedCustomerFields:
    company_name: str | None
    email: str | None
    country: str | None


@dataclass(frozen=True)
class FieldReconciliation:
    field: Literal["company_name", "email", "country"]
    status: FieldReconciliationStatus
    canonical_value: str | None
    source_value: str | None


@dataclass(frozen=True)
class CustomerReconciliation:
    status: CustomerReconciliationStatus
    mismatches: list[str]
    missing: list[str]


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = " ".join(value.strip().split())

    return normalized.lower() if normalized else None


def _normalize_email(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().lower()

    return normalized or None


def _normalize_country(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().upper()

    return normalized or None


def normalize_customer_fields(
    *,
    company_name: str | None,
    email: str | None,
    country: str | None,
) -> NormalizedCustomerFields:
    return NormalizedCustomerFields(
        company_name=_normalize_text(company_name),
        email=_normalize_email(email),
        country=_normalize_country(country),
    )


def _compare_field(
    *,
    field: Literal["company_name", "email", "country"],
    canonical_value: str | None,
    source_value: str | None,
) -> FieldReconciliation:
    if canonical_value is None and source_value is None:
        status = FieldReconciliationStatus.MATCH

    elif canonical_value is None:
        status = FieldReconciliationStatus.MISSING_ON_CANONICAL

    elif source_value is None:
        status = FieldReconciliationStatus.MISSING_ON_SOURCE

    elif canonical_value == source_value:
        status = FieldReconciliationStatus.MATCH

    else:
        status = FieldReconciliationStatus.MISMATCH

    return FieldReconciliation(
        field=field,
        status=status,
        canonical_value=canonical_value,
        source_value=source_value,
    )


def compare_customer_fields(
    *,
    canonical: NormalizedCustomerFields,
    source: NormalizedCustomerFields,
) -> dict[str, FieldReconciliation]:
    return {
        "company_name": _compare_field(
            field="company_name",
            canonical_value=canonical.company_name,
            source_value=source.company_name,
        ),
        "email": _compare_field(
            field="email",
            canonical_value=canonical.email,
            source_value=source.email,
        ),
        "country": _compare_field(
            field="country",
            canonical_value=canonical.country,
            source_value=source.country,
        ),
    }


def summarize_customer_reconciliation(
    fields: dict[str, FieldReconciliation],
) -> CustomerReconciliation:
    mismatches = [
        name
        for name, result in fields.items()
        if result.status is FieldReconciliationStatus.MISMATCH
    ]

    missing = [
        name
        for name, result in fields.items()
        if result.status
        in {
            FieldReconciliationStatus.MISSING_ON_SOURCE,
            FieldReconciliationStatus.MISSING_ON_CANONICAL,
        }
    ]

    if mismatches:
        status = CustomerReconciliationStatus.MISMATCH
    elif missing:
        status = CustomerReconciliationStatus.INCOMPLETE
    else:
        status = CustomerReconciliationStatus.MATCHED

    return CustomerReconciliation(
        status=status,
        mismatches=mismatches,
        missing=missing,
    )


@dataclass(frozen=True)
class CustomerSourceReconciliation:
    source: str
    entity_type: str
    status: CustomerReconciliationStatus
    mismatches: list[str]
    missing: list[str]
    fields: dict[str, FieldReconciliation]

    def classify_ownership(
        self,
        *,
        policy,
    ):
        from apps.gpuaas.app.services.customer_field_ownership_classification import (
            classify_reconciliation_fields,
        )

        return classify_reconciliation_fields(
            fields=self.fields,
            source=self.source,
            policy=policy,
        )


def reconcile_customer_source(
    *,
    customer,
    source: str,
    entity_type: str,
    source_record: dict,
) -> CustomerSourceReconciliation:
    canonical = normalize_customer_fields(
        company_name=customer.company_name,
        email=customer.email,
        country=customer.country,
    )

    source_fields = normalize_customer_fields(
        company_name=source_record.get("company_name"),
        email=source_record.get("email"),
        country=source_record.get("country"),
    )

    fields = compare_customer_fields(
        canonical=canonical,
        source=source_fields,
    )

    summary = summarize_customer_reconciliation(fields)

    return CustomerSourceReconciliation(
        source=source,
        entity_type=entity_type,
        status=summary.status,
        mismatches=summary.mismatches,
        missing=summary.missing,
        fields=fields,
    )
