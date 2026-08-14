from fastapi import FastAPI

from apps.gpuaas.app.api.routes.allocations import router as allocations_router
from apps.gpuaas.app.api.routes.capacity import router as capacity_router
from apps.gpuaas.app.api.routes.customers import router as customers_router

app = FastAPI(
    title="GPUFlow GPUaaS",
    description="Mock GPU cloud provider API for GPUFlow",
    version="0.1.0",
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
    capacity_router,
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
