from typing import Any


class PipedriveOrganizationReconciliationAdapter:
    def to_customer_record(
        self,
        organization: dict[str, Any],
    ) -> dict[str, str | None]:
        return {
            "company_name": organization.get("name"),
            "email": organization.get("email"),
            "country": organization.get("country"),
        }
