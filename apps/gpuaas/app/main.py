from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.gpuaas.app.api.routes.allocations import (
    router as allocations_router,
)
from apps.gpuaas.app.api.routes.analytics import (
    router as analytics_router,
)
from apps.gpuaas.app.api.routes.billing import (
    router as billing_router,
)
from apps.gpuaas.app.api.routes.capacity import (
    router as capacity_router,
)
from apps.gpuaas.app.api.routes.customers import (
    router as customers_router,
)
from apps.gpuaas.app.api.routes.invoices import (
    router as invoices_router,
)
from apps.gpuaas.app.api.routes.jobs import (
    router as jobs_router,
)
from apps.gpuaas.app.api.routes.usage import (
    router as usage_router,
)
from apps.gpuaas.app.api.routes.xero import (
    router as xero_router,
)
from apps.gpuaas.app.api.routes.xero_invoices import (
    router as xero_invoices_router,
)

app = FastAPI(
    title="GPUFlow GPUaaS",
    description="Mock GPU cloud provider API for GPUFlow",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    customers_router,
    prefix="/api/v1",
)

app.include_router(
    allocations_router,
    prefix="/api/v1",
)

app.include_router(
    analytics_router,
    prefix="/api/v1",
)

app.include_router(
    billing_router,
    prefix="/api/v1",
)

app.include_router(
    capacity_router,
    prefix="/api/v1",
)

app.include_router(
    invoices_router,
    prefix="/api/v1",
)

app.include_router(
    jobs_router,
    prefix="/api/v1",
)

app.include_router(
    usage_router,
    prefix="/api/v1",
)

app.include_router(
    xero_router,
    prefix="/api/v1",
)

app.include_router(
    xero_invoices_router,
    prefix="/api/v1",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "service": "gpuaas",
        "status": "healthy",
    }


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "GPUFlow GPUaaS",
        "version": "0.1.0",
    }
