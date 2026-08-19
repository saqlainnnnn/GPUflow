from apps.gpuaas.app.models.customer_data_quality_audit import (
    CustomerDataQualityAudit,
)


class CustomerDataQualityAuditRepository:
    def __init__(self, session) -> None:
        self.session = session

    async def create(
        self,
        audit: CustomerDataQualityAudit,
    ) -> CustomerDataQualityAudit:
        self.session.add(audit)
        await self.session.flush()
        await self.session.refresh(audit)
        return audit
