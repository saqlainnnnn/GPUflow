from apps.gpuaas.app.repositories.customer import (
    CustomerRepository,
)
from apps.gpuaas.app.services.customer_duplicate_detection import (
    CustomerDuplicateDetectionService,
)
from apps.gpuaas.app.services.customer_duplicate_issue import (
    CustomerDuplicateIssueService,
)


class CustomerDuplicateScanService:
    def __init__(
        self,
        *,
        customer_repository: CustomerRepository,
        detector: CustomerDuplicateDetectionService,
        issue_service: CustomerDuplicateIssueService,
    ) -> None:
        self.customers = customer_repository
        self.detector = detector
        self.issue_service = issue_service

    async def scan(self) -> list:
        customers = await self.customers.list_customers(
            offset=0,
            limit=10000,
        )

        records = [
            {
                "id": str(customer.id),
                "company_name": customer.company_name,
                "email": customer.email,
            }
            for customer in customers
        ]

        candidates = self.detector.find_candidates(
            records
        )

        unique_candidates = []
        seen: set[tuple[str, str]] = set()

        for candidate in candidates:
            pair = tuple(
                sorted(
                    [
                        str(candidate.left_id),
                        str(candidate.right_id),
                    ]
                )
            )

            if pair in seen:
                continue

            seen.add(pair)
            unique_candidates.append(candidate)

        current_pairs = {
            tuple(
                sorted(
                    [
                        str(candidate.left_id),
                        str(candidate.right_id),
                    ]
                )
            )
            for candidate in unique_candidates
        }

        issues = []

        for candidate in unique_candidates:
            issue = await self.issue_service.open_candidate(
                candidate
            )

            issues.append(issue)

        open_issues = (
            await self.issue_service
            .list_open_duplicate_candidates()
        )

        for issue in open_issues:
            pair = tuple(
                sorted(
                    [
                        str(issue.customer_id),
                        str(
                            issue.details[
                                "right_customer_id"
                            ]
                        ),
                    ]
                )
            )

            if pair in current_pairs:
                continue

            left_id = str(issue.customer_id)
            right_id = str(
                issue.details[
                    "right_customer_id"
                ]
            )

            candidate = type(
                "DuplicateCandidate",
                (),
                {
                    "left_id": left_id,
                    "right_id": right_id,
                    "match_reasons": list(
                        issue.details.get(
                            "match_reasons",
                            [],
                        )
                    ),
                },
            )()

            await self.issue_service.resolve_candidate(
                candidate
            )

        return issues
