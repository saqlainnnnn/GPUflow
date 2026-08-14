from fastapi import FastAPI

from apps.integration_hub.app.api.routes.events import router as events_router
from apps.integration_hub.app.api.routes.pipedrive import (
    router as pipedrive_router,
)

app = FastAPI(
    title="GPUFlow Integration Hub",
    description="Event-driven integration layer for GPUFlow",
    version="0.1.0",
)

app.include_router(
    events_router,
    prefix="/api/v1",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "service": "integration-hub",
        "status": "healthy",
    }


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "GPUFlow Integration Hub",
        "version": "0.1.0",
    }


app.include_router(
    pipedrive_router,
    prefix="/api/v1",
)
