from base64 import b64encode
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from apps.gpuaas.app.core.config import get_settings
from apps.gpuaas.app.repositories.xero_connection import (
    XeroConnectionRepository,
)
from apps.gpuaas.app.services.xero_connection import (
    XeroConnectionNotFoundError,
)

XERO_TOKEN_URL = "https://identity.xero.com/connect/token"

REFRESH_BUFFER_SECONDS = 60


def _basic_auth_header() -> str:
    settings = get_settings()

    credentials = (f"{settings.xero_client_id}:{settings.xero_client_secret}").encode()

    return "Basic " + b64encode(credentials).decode()


async def refresh_xero_tokens(
    refresh_token: str,
) -> dict[str, Any]:
    settings = get_settings()

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            XERO_TOKEN_URL,
            headers={
                "Authorization": _basic_auth_header(),
                "Content-Type": ("application/x-www-form-urlencoded"),
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )

    response.raise_for_status()

    return response.json()


async def get_valid_connection(
    session: AsyncSession,
    customer_id: UUID,
):
    repository = XeroConnectionRepository(session)

    connection = await repository.get_by_customer(customer_id)

    if connection is None:
        raise XeroConnectionNotFoundError(f"No Xero connection for customer '{customer_id}'")

    now = datetime.now(UTC)

    if connection.expires_at > (now + timedelta(seconds=REFRESH_BUFFER_SECONDS)):
        return connection

    tokens = await refresh_xero_tokens(connection.refresh_token)

    connection.access_token = tokens["access_token"]
    connection.refresh_token = tokens.get(
        "refresh_token",
        connection.refresh_token,
    )
    connection.expires_at = now + timedelta(seconds=int(tokens["expires_in"]))

    await session.commit()
    await session.refresh(connection)

    return connection
