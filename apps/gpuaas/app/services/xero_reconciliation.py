from typing import Any


class XeroContactReconciliationAdapter:
    def to_customer_record(
        self,
        contact: dict[str, Any],
    ) -> dict[str, str | None]:
        return {
            "company_name": contact.get("Name"),
            "email": contact.get("EmailAddress"),
            "country": contact.get("Country"),
        }
