from apps.gpuaas.app.models.kyb_audit import KYBAudit
from apps.gpuaas.app.repositories.kyb_audit import (
    KYBAuditRepository,
)
from apps.gpuaas.app.services.kyb import (
    KYBDecision,
    KYBScreeningResult,
)


class KYBAuditService:
    def __init__(
        self,
        *,
        repository: KYBAuditRepository,
    ) -> None:
        self.repository = repository

    async def record_screening(
        self,
        *,
        customer_id,
        company_name: str,
        country: str,
        result: KYBScreeningResult,
    ) -> None:
        input_snapshot = {
            "company_name": company_name,
            "country": country,
        }

        if result.checks:
            for check in result.checks:
                audit = KYBAudit(
                    customer_id=customer_id,
                    check_type=check.check_type,
                    input_snapshot=input_snapshot,
                    decision=result.decision.value,
                    reason=check.reason,
                    reviewer=None,
                )

                await self.repository.create(audit)

            return

        audit = KYBAudit(
            customer_id=customer_id,
            check_type="screening",
            input_snapshot=input_snapshot,
            decision=KYBDecision.CLEAR.value,
            reason="No screening violations detected.",
            reviewer=None,
        )

        await self.repository.create(audit)
