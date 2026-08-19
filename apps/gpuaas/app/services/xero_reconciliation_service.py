from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.integrations.xero.client import XeroClient
from apps.gpuaas.app.integrations.xero.token_manager import (
    get_valid_connection,
)
from apps.gpuaas.app.repositories.customer import (
    CustomerRepository,
)
from apps.gpuaas.app.repositories.customer_identity import (
    CustomerIdentityRepository,
)
from apps.gpuaas.app.services.customer_reconciliation import (
    CustomerSourceReconciliation,
    reconcile_customer_source,
)
from apps.gpuaas.app.services.xero_reconciliation import (
    XeroContactReconciliationAdapter,
)


class XeroReconciliationService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        customer_repository: CustomerRepository,
        identity_repository: CustomerIdentityRepository,
    ) -> None:
        self.session = session
        self.customers = customer_repository
        self.identities = identity_repository

    async def reconcile_contact(
        self,
        *,
        customer_id: UUID,
        contact_id: str,
    ) -> CustomerSourceReconciliation:
        customer = await self.customers.get_by_id(customer_id)

        if customer is None:
            raise ValueError(
                f"Customer '{customer_id}' not found"
            )

        identity = (
            await self.identities.find_by_external_identity(
                source="xero",
                entity_type="contact",
                external_id=contact_id,
            )
        )

        if identity is None:
            raise ValueError(
                "Customer identity is not linked"
            )

        if identity.customer_id != customer_id:
            raise ValueError(
                "Customer identity belongs to another customer"
            )

        connection = await get_valid_connection(
            self.session,
            customer_id,
        )

        client = XeroClient(
            access_token=connection.access_token,
            tenant_id=connection.tenant_id,
        )

        contact = await client.get_contact(contact_id)

        adapter = XeroContactReconciliationAdapter()

        source_record = adapter.to_customer_record(
            contact
        )

        return reconcile_customer_source(
            customer=customer,
            source="xero",
            entity_type="contact",
            source_record=source_record,
        )
