import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.api.dependencies import get_db
from apps.gpuaas.app.core.redis import get_redis
from apps.gpuaas.app.integrations.xero.oauth import (
    build_authorization_url,
    exchange_code_for_tokens,
    get_connections,
)
from apps.gpuaas.app.schemas.xero import (
    XeroCallbackResponse,
    XeroConnectionResponse,
)
from apps.gpuaas.app.services.xero_connection import (
    XeroConnectionNotFoundError,
    XeroConnectionService,
)

router = APIRouter(
    prefix="/xero",
    tags=["xero"],
)

STATE_TTL_SECONDS = 600


@router.get("/connect")
async def connect_xero(
    customer_id: UUID,
) -> RedirectResponse:
    state = secrets.token_urlsafe(32)

    redis = get_redis()

    try:
        await redis.set(
            f"gpuflow:xero:oauth:{state}",
            str(customer_id),
            ex=STATE_TTL_SECONDS,
        )
    finally:
        await redis.aclose()

    return RedirectResponse(url=build_authorization_url(state))


@router.get(
    "/callback",
    response_model=XeroCallbackResponse,
)
async def xero_callback(
    code: str,
    state: str,
    session: AsyncSession = Depends(get_db),
) -> XeroCallbackResponse:
    redis = get_redis()

    try:
        customer_id_raw = await redis.get(f"gpuflow:xero:oauth:{state}")

        if customer_id_raw is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired Xero OAuth state",
            )

        await redis.delete(f"gpuflow:xero:oauth:{state}")
    finally:
        await redis.aclose()

    customer_id = UUID(customer_id_raw)

    tokens = await exchange_code_for_tokens(code)

    connections = await get_connections(tokens["access_token"])

    if not connections:
        raise HTTPException(
            status_code=400,
            detail="No Xero tenant was authorized",
        )

    connection = connections[0]

    token_type = tokens.get("token_type")

    if token_type and token_type.lower() != "bearer":
        raise HTTPException(
            status_code=502,
            detail="Unexpected Xero token type",
        )

    service = XeroConnectionService(session)

    saved = await service.save_tokens(
        customer_id=customer_id,
        tenant_id=connection["tenantId"],
        tenant_name=connection.get("tenantName"),
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        expires_in=int(tokens["expires_in"]),
    )

    return XeroCallbackResponse(
        connected=True,
        tenant_id=saved.tenant_id,
        tenant_name=saved.tenant_name,
    )


@router.get(
    "/connections/{customer_id}",
    response_model=XeroConnectionResponse,
)
async def get_xero_connection(
    customer_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> XeroConnectionResponse:
    service = XeroConnectionService(session)

    try:
        connection = await service.get_connection(customer_id)
    except XeroConnectionNotFoundError:
        return XeroConnectionResponse(
            connected=False,
            tenant_id=None,
            tenant_name=None,
        )

    return XeroConnectionResponse(
        connected=True,
        tenant_id=connection.tenant_id,
        tenant_name=connection.tenant_name,
    )
