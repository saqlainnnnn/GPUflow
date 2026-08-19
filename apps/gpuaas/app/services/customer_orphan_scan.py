class CustomerOrphanScanService:
    def __init__(
        self,
        *,
        pipedrive_scanner,
        xero_scanner,
    ) -> None:
        self.pipedrive_scanner = pipedrive_scanner
        self.xero_scanner = xero_scanner

    async def scan_all(self) -> list:
        pipedrive_results = (
            await self.pipedrive_scanner.scan()
        )

        xero_results = (
            await self.xero_scanner.scan()
        )

        return [
            *pipedrive_results,
            *xero_results,
        ]
