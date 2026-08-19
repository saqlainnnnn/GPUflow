from typing import Any


class PipedriveCustomerReconciliationHandler:
    def __init__(
        self,
        *,
        pipedrive: Any,
        adapter: Any,
        runner: Any,
        ownership_policy: Any,
    ) -> None:
        self.pipedrive = pipedrive
        self.adapter = adapter
        self.runner = runner
        self.ownership_policy = ownership_policy

    async def reconcile(
        self,
        identity,
    ):
        if (
            identity.source != "pipedrive"
            or identity.entity_type != "organization"
        ):
            raise ValueError(
                "unsupported Pipedrive identity"
            )

        organization_id = int(
            identity.external_id
        )

        organization = (
            await self.pipedrive.get_organization(
                organization_id
            )
        )

        source_record = (
            self.adapter.to_customer_record(
                organization
            )
        )

        return await self.runner.reconcile_and_persist(
            customer_id=identity.customer_id,
            source="pipedrive",
            entity_type="organization",
            external_id=identity.external_id,
            source_record=source_record,
            adapter=self.adapter,
            ownership_policy=self.ownership_policy,
        )
