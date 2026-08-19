from apps.integration_hub.app.integrations.pipedrive.client import (
    PipedriveClient,
)


class PipedriveOrphanScanner:
    def __init__(
        self,
        *,
        pipedrive: PipedriveClient,
        orphan_reconciliation,
    ) -> None:
        self.pipedrive = pipedrive
        self.orphan_reconciliation = orphan_reconciliation

    async def scan(self):
        organizations = (
            await self.pipedrive.list_organizations()
        )

        records = [
            {
                "source": "pipedrive",
                "entity_type": "organization",
                "external_id": str(
                    organization["id"]
                ),
            }
            for organization in organizations
        ]

        return await self.orphan_reconciliation.process_records(
            records
        )
