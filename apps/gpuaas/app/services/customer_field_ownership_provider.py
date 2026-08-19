from apps.gpuaas.app.services.customer_field_ownership import (
    CustomerFieldOwnershipPolicy,
)


class CustomerFieldOwnershipProvider:
    def for_customer(
        self,
    ) -> CustomerFieldOwnershipPolicy:
        return CustomerFieldOwnershipPolicy(
            {
                "company_name": "pipedrive",
                "email": "pipedrive",
                "country": "pipedrive",
            }
        )
