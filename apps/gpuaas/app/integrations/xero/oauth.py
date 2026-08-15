from base64 import b64encode
from typing import Any
from urllib.parse import urlencode

import httpx

from apps.gpuaas.app.core.config import get_settings

XERO_AUTHORIZE_URL = "https://login.xero.com/identity/connect/authorize"

XERO_TOKEN_URL = "https://identity.xero.com/connect/token"

XERO_CONNECTIONS_URL = "https://api.xero.com/connections"


def build_authorization_url(
    state: str,
) -> str:
    settings = get_settings()

    params = {
        "response_type": "code",
        "client_id": settings.xero_client_id,
        "redirect_uri": settings.xero_redirect_uri,
        "scope": settings.xero_scopes,
        "state": state,
    }

    return f"{XERO_AUTHORIZE_URL}?{urlencode(params)}"


def _basic_auth_header() -> str:
    settings = get_settings()

    credentials = (f"{settings.xero_client_id}:{settings.xero_client_secret}").encode()

    return "Basic " + b64encode(credentials).decode()


async def exchange_code_for_tokens(
    code: str,
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
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.xero_redirect_uri,
            },
        )

    response.raise_for_status()

    return response.json()


async def get_connections(
    access_token: str,
) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            XERO_CONNECTIONS_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise RuntimeError("Unexpected Xero connections response")

    return data
