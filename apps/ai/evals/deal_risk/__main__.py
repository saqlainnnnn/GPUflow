import asyncio
from pathlib import Path

from apps.ai.evals.deal_risk.dataset import (
    load_deal_risk_eval_dataset,
)


async def main() -> None:
    dataset = load_deal_risk_eval_dataset(
        Path("apps/ai/evals/deal_risk/cases.json"),
    )

    print("Deal Risk Regression")
    print("====================")
    print(f"Cases: {len(dataset.cases)}")
    print()
    print("Dataset loaded successfully.")
    print(
        f"Deal ID: {dataset.runner_config.deal_id}"
    )
    print(
        f"Organization ID: {dataset.runner_config.organization_id}"
    )
    print(
        f"Customer ID: {dataset.runner_config.customer_id}"
    )
    print(
        f"Today: {dataset.runner_config.today}"
    )


if __name__ == "__main__":
    asyncio.run(main())
