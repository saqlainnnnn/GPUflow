import asyncio
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from apps.gpuaas.app.db.session import AsyncSessionLocal
from apps.gpuaas.app.models.allocation import GPUAllocation
from apps.gpuaas.app.models.capacity import GPUCapacity
from apps.gpuaas.app.models.customer import Customer
from apps.gpuaas.app.models.job import GPUJob
from apps.gpuaas.app.models.usage_event import GPUUsageEvent


@dataclass(frozen=True)
class CustomerProfile:
    name: str
    domain: str
    behavior: str
    base_utilization: float
    growth_rate: float
    gpu_count: int
    gpu_type: str
    region: str
    country: str


PROFILES = [
    CustomerProfile(
        name="Acme AI",
        domain="acme.ai",
        behavior="expanding",
        base_utilization=0.70,
        growth_rate=0.025,
        gpu_count=8,
        gpu_type="H100",
        region="us-east",
        country="US",
    ),
    CustomerProfile(
        name="Neural Labs",
        domain="neural-labs.ai",
        behavior="declining",
        base_utilization=0.82,
        growth_rate=-0.02,
        gpu_count=8,
        gpu_type="H100",
        region="us-east",
        country="US",
    ),
    CustomerProfile(
        name="Vector AI",
        domain="vector.ai",
        behavior="stable",
        base_utilization=0.68,
        growth_rate=0.001,
        gpu_count=4,
        gpu_type="A100",
        region="eu-west",
        country="DE",
    ),
    CustomerProfile(
        name="ModelWorks",
        domain="modelworks.ai",
        behavior="bursty",
        base_utilization=0.50,
        growth_rate=0.005,
        gpu_count=8,
        gpu_type="H100",
        region="us-west",
        country="US",
    ),
    CustomerProfile(
        name="InferenceCo",
        domain="inferenceco.ai",
        behavior="high_utilization",
        base_utilization=0.90,
        growth_rate=0.01,
        gpu_count=16,
        gpu_type="H100",
        region="us-east",
        country="US",
    ),
    CustomerProfile(
        name="ScaleForge",
        domain="scaleforge.ai",
        behavior="expanding",
        base_utilization=0.62,
        growth_rate=0.03,
        gpu_count=16,
        gpu_type="H200",
        region="us-west",
        country="US",
    ),
    CustomerProfile(
        name="QuietCompute",
        domain="quietcompute.ai",
        behavior="declining",
        base_utilization=0.65,
        growth_rate=-0.015,
        gpu_count=4,
        gpu_type="A100",
        region="eu-west",
        country="DE",
    ),
    CustomerProfile(
        name="TrainOps",
        domain="trainops.ai",
        behavior="bursty",
        base_utilization=0.45,
        growth_rate=0.008,
        gpu_count=12,
        gpu_type="H100",
        region="us-east",
        country="US",
    ),
    CustomerProfile(
        name="SteadyInference",
        domain="steadyinference.ai",
        behavior="high_utilization",
        base_utilization=0.88,
        growth_rate=0.006,
        gpu_count=12,
        gpu_type="H100",
        region="eu-west",
        country="DE",
    ),
    CustomerProfile(
        name="StableScale",
        domain="stablescale.ai",
        behavior="stable",
        base_utilization=0.74,
        growth_rate=0.0,
        gpu_count=8,
        gpu_type="A100",
        region="us-west",
        country="US",
    ),
]


def utilization_for_day(
    profile: CustomerProfile,
    day_index: int,
    rng: random.Random,
) -> float:
    value = profile.base_utilization

    value *= 1 + profile.growth_rate * day_index

    if profile.behavior == "expanding":
        value += day_index * 0.004

    elif profile.behavior == "declining":
        value -= day_index * 0.004

    elif profile.behavior == "bursty":
        weekday = day_index % 7

        if weekday in (0, 1, 2):
            value += 0.18
        elif weekday in (5, 6):
            value -= 0.16

    elif profile.behavior == "high_utilization":
        value += min(day_index * 0.002, 0.06)

    value += rng.uniform(-0.04, 0.04)

    return round(max(0.05, min(0.99, value)), 4)


def gpu_hours_for_day(
    gpu_count: int,
    utilization: float,
    rng: random.Random,
) -> float:
    theoretical_max = gpu_count * 24
    variation = rng.uniform(0.92, 1.08)

    return round(
        max(0.1, theoretical_max * utilization * variation),
        4,
    )


def job_status(rng: random.Random) -> tuple[str, str | None]:
    value = rng.random()

    if value < 0.94:
        return "completed", None

    if value < 0.98:
        return "failed", rng.choice(
            [
                "out_of_memory",
                "node_failure",
                "image_pull_failure",
                "timeout",
            ]
        )

    return "running", None


async def get_or_create_capacity(
    session,
    region: str,
    gpu_type: str,
) -> GPUCapacity:
    result = await session.execute(
        select(GPUCapacity).where(
            GPUCapacity.region == region,
            GPUCapacity.gpu_type == gpu_type,
        )
    )

    capacity = result.scalar_one_or_none()

    if capacity is not None:
        return capacity

    capacity = GPUCapacity(
        region=region,
        gpu_type=gpu_type,
        total_gpus=1000,
        allocated_gpus=0,
        status="active",
    )

    session.add(capacity)
    await session.flush()

    return capacity


async def get_or_create_customer(
    session,
    profile: CustomerProfile,
    index: int,
) -> Customer:
    external_id = f"seed_customer_{index:03d}"

    result = await session.execute(
        select(Customer).where(
            Customer.external_id == external_id
        )
    )

    customer = result.scalar_one_or_none()

    if customer is not None:
        return customer

    customer = Customer(
        external_id=external_id,
        company_name=profile.name,
        email=f"infra@{profile.domain}",
        country=profile.country,
        status="active",
    )

    session.add(customer)
    await session.flush()

    return customer


async def get_or_create_allocation(
    session,
    customer: Customer,
    profile: CustomerProfile,
) -> GPUAllocation:
    result = await session.execute(
        select(GPUAllocation).where(
            GPUAllocation.customer_id == customer.id,
            GPUAllocation.gpu_type == profile.gpu_type,
            GPUAllocation.region == profile.region,
        )
    )

    allocation = result.scalar_one_or_none()

    if allocation is not None:
        return allocation

    allocation = GPUAllocation(
        customer_id=customer.id,
        gpu_type=profile.gpu_type,
        gpu_count=profile.gpu_count,
        region=profile.region,
        status="active",
    )

    session.add(allocation)
    await session.flush()

    return allocation


async def generate_customer_telemetry(
    session,
    customer: Customer,
    allocation: GPUAllocation,
    profile: CustomerProfile,
    days: int,
    rng: random.Random,
) -> tuple[int, int]:
    now = datetime.now(UTC)

    created_events = 0
    created_jobs = 0

    for day_index in range(days):
        day = now - timedelta(days=days - 1 - day_index)

        utilization = utilization_for_day(
            profile,
            day_index,
            rng,
        )

        gpu_hours = gpu_hours_for_day(
            allocation.gpu_count,
            utilization,
            rng,
        )

        event_id = (
            f"telemetry-{customer.external_id}-"
            f"{day.strftime('%Y%m%d')}"
        )

        existing_event = await session.execute(
            select(GPUUsageEvent).where(
                GPUUsageEvent.event_id == event_id
            )
        )

        if existing_event.scalar_one_or_none() is None:
            session.add(
                GPUUsageEvent(
                    event_id=event_id,
                    customer_id=customer.id,
                    allocation_id=allocation.id,
                    gpu_type=allocation.gpu_type,
                    gpu_hours=gpu_hours,
                    utilization=utilization,
                    timestamp=day.replace(
                        hour=23,
                        minute=30,
                        second=0,
                        microsecond=0,
                    ),
                )
            )

            created_events += 1

        job_count = max(
            1,
            round(allocation.gpu_count * utilization / 2),
        )

        for job_index in range(job_count):
            job_external_id = (
                f"telemetry-job-{customer.external_id}-"
                f"{day.strftime('%Y%m%d')}-{job_index}"
            )

            existing_job = await session.execute(
                select(GPUJob).where(
                    GPUJob.external_id == job_external_id
                )
            )

            if existing_job.scalar_one_or_none() is not None:
                continue

            status, failure_reason = job_status(rng)

            session.add(
                GPUJob(
                    external_id=job_external_id,
                    customer_id=customer.id,
                    allocation_id=allocation.id,
                    gpu_type=allocation.gpu_type,
                    gpu_count=rng.randint(
                        1,
                        allocation.gpu_count,
                    ),
                    status=status,
                    duration_seconds=rng.randint(
                        300,
                        21_600,
                    ),
                    failure_reason=failure_reason,
                )
            )

            created_jobs += 1

    return created_events, created_jobs


async def reconcile_capacity(session) -> None:
    result = await session.execute(
        select(GPUCapacity)
    )

    capacities = result.scalars().all()

    for capacity in capacities:
        allocations = await session.execute(
            select(GPUAllocation).where(
                GPUAllocation.region == capacity.region,
                GPUAllocation.gpu_type == capacity.gpu_type,
                GPUAllocation.status == "active",
            )
        )

        capacity.allocated_gpus = sum(
            allocation.gpu_count
            for allocation in allocations.scalars().all()
        )


async def main() -> None:
    rng = random.Random(42)

    async with AsyncSessionLocal() as session:
        total_events = 0
        total_jobs = 0

        for index, profile in enumerate(PROFILES, start=1):
            await get_or_create_capacity(
                session,
                profile.region,
                profile.gpu_type,
            )

            customer = await get_or_create_customer(
                session,
                profile,
                index,
            )

            allocation = await get_or_create_allocation(
                session,
                customer,
                profile,
            )

            events, jobs = await generate_customer_telemetry(
                session,
                customer,
                allocation,
                profile,
                days=30,
                rng=rng,
            )

            total_events += events
            total_jobs += jobs

        await reconcile_capacity(session)
        await session.commit()

    print("GPUFlow telemetry generation complete.")
    print(f"Created usage events: {total_events}")
    print(f"Created jobs:         {total_jobs}")


if __name__ == "__main__":
    asyncio.run(main())
