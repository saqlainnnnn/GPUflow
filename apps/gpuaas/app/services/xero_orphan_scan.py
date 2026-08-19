from apps.gpuaas.app.integrations.xero.client import XeroClient


class XeroOrphanScanner:
    def __init__(
        self,
        *,
        xero: XeroClient,
        orphan_reconciliation,
    ) -> None:
        self.xero = xero
        self.orphan_reconciliation = orphan_reconciliation

    async def scan(self):
        contacts = await self.xero.list_contacts()

        records = [
            {
                "source": "xero",
                "entity_type": "contact",
                "external_id": str(
                    contact["ContactID"]
                ),
            }
            for contact in contacts
            if contact.get("ContactID")
        ]

        return await self.orphan_reconciliation.process_records(
            records
        )
