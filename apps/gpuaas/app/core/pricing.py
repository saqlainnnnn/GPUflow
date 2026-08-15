from decimal import Decimal

GPU_HOURLY_RATES: dict[str, Decimal] = {
    "A100": Decimal("2.50"),
    "H100": Decimal("4.00"),
    "H200": Decimal("5.00"),
}


def get_gpu_hourly_rate(gpu_type: str) -> Decimal:
    try:
        return GPU_HOURLY_RATES[gpu_type.upper()]
    except KeyError as exc:
        raise ValueError(f"No pricing configured for GPU type '{gpu_type}'") from exc
