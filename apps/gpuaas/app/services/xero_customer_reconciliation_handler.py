from typing import Any, Callable

from apps.gpuaas.app.integrations.xero.client import XeroClient
from apps.gpuaas.app.integrations.xero.token_manager import (
    get_valid_connection,
)


class XeroCustomerReconciliationHandler:
    def __init__(
        self,
        *,
        session: Any,
        adapter: Any,
        runner: Any,
        ownership_policy: Any,
        client_factory: Callable[..., XeroClient] = XeroClient,
    ) -> None:
        self.session = session
        self.adapter = adapter
        self.runner = runner
        self.ownership_policy = ownership_policy
        self.client_factory = client_factory

    async def reconcile(
        self,
        identity,
    ):
        if (
            identity.source != "xero"
            or identity.entity_type != "contact"
        ):
            raise ValueError(
                "unsupported Xero identity"
            )

        connection = await get_valid_connection(
            self.session,
            identity.customer_id,
        )

        xero = self.client_factory(
            access_token=connection.access_token,
            tenant_id=connection.tenant_id,
        )

        contact = await xero.get_contact(
            identity.external_id
        )

        source_record = (
            self.adapter.to_customer_record(
                contact
            )
        )

        return await self.runner.reconcile_and_persist(
            customer_id=identity.customer_id,
            source="xero",
            entity_type="contact",
            external_id=identity.external_id,
            source_record=source_record,
            adapter=self.adapter,
            ownership_policy=self.ownership_policy,
        )
