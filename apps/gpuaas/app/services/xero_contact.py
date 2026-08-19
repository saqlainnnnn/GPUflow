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
from apps.gpuaas.app.services.customer_identity import (
    CustomerIdentityService,
)
from apps.gpuaas.app.services.xero_connection import (
    XeroConnectionService,
)


class XeroContactService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session
        self.customers = CustomerRepository(session)
        self.connections = XeroConnectionService(session)

        self.identities = CustomerIdentityService(
            CustomerIdentityRepository(session)
        )

    async def get_or_create_contact(
        self,
        customer_id: UUID,
    ) -> str:
        customer = await self.customers.get_by_id(customer_id)

        if customer is None:
            raise ValueError(f"Customer '{customer_id}' not found")

        connection = await get_valid_connection(
            self.session,
            customer_id,
        )

        if connection.xero_contact_id:
            contact_id = connection.xero_contact_id

            await self.identities.link_identity(
                customer_id=customer_id,
                source="xero",
                entity_type="contact",
                external_id=contact_id,
            )

            return contact_id

        client = XeroClient(
            access_token=connection.access_token,
            tenant_id=connection.tenant_id,
        )

        contact = await client.find_contact_by_email(
            customer.email
        )

        if contact is None:
            contact = await client.find_contact_by_name(
                customer.company_name
            )

        if contact is None:
            result = await client.create_contact(
                name=customer.company_name,
                email=customer.email,
            )

            contacts = result.get(
                "Contacts",
                [],
            )

            if not contacts:
                raise RuntimeError(
                    "Xero contact creation returned no contact"
                )

            contact = contacts[0]

        contact_id = contact.get("ContactID")

        if not contact_id:
            raise RuntimeError(
                "Xero contact response missing ContactID"
            )

        await self.connections.set_contact_id(
            customer_id,
            contact_id,
        )

        await self.identities.link_identity(
            customer_id=customer_id,
            source="xero",
            entity_type="contact",
            external_id=contact_id,
        )

        return contact_id
