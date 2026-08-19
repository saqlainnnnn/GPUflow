from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.gpuaas.app.api.dependencies import get_db
from apps.gpuaas.app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_link_customer_identity(client):
    customer_external_id = f"identity_test_{uuid4()}"
    identity_external_id = str(uuid4())

    create_response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": customer_external_id,
            "company_name": "Identity Test AI",
            "email": "identity@test.ai",
            "country": "IN",
        },
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/customers/{customer_id}/identities",
        json={
            "source": "pipedrive",
            "entity_type": "organization",
            "external_id": identity_external_id,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == customer_id
    assert data["source"] == "pipedrive"
    assert data["entity_type"] == "organization"
    assert data["external_id"] == identity_external_id


@pytest.mark.asyncio
async def test_link_customer_identity_is_idempotent(client):
    customer_external_id = f"idempotent_identity_{uuid4()}"
    identity_external_id = str(uuid4())

    create_response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": customer_external_id,
            "company_name": "Idempotent Identity AI",
            "email": "idempotent@test.ai",
            "country": "IN",
        },
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    payload = {
        "source": "pipedrive",
        "entity_type": "organization",
        "external_id": identity_external_id,
    }

    first_response = await client.post(
        f"/api/v1/customers/{customer_id}/identities",
        json=payload,
    )

    second_response = await client.post(
        f"/api/v1/customers/{customer_id}/identities",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    assert first_response.json()["id"] == second_response.json()["id"]


@pytest.mark.asyncio
async def test_link_customer_identity_rejects_identity_owned_by_other_customer(
    client,
):
    first_external_id = f"identity_owner_a_{uuid4()}"
    second_external_id = f"identity_owner_b_{uuid4()}"
    identity_external_id = str(uuid4())

    first_response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": first_external_id,
            "company_name": "Identity Owner A",
            "email": "a@test.ai",
            "country": "IN",
        },
    )

    second_response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": second_external_id,
            "company_name": "Identity Owner B",
            "email": "b@test.ai",
            "country": "IN",
        },
    )

    first_customer_id = first_response.json()["id"]
    second_customer_id = second_response.json()["id"]

    payload = {
        "source": "pipedrive",
        "entity_type": "organization",
        "external_id": identity_external_id,
    }

    first_link = await client.post(
        f"/api/v1/customers/{first_customer_id}/identities",
        json=payload,
    )

    second_link = await client.post(
        f"/api/v1/customers/{second_customer_id}/identities",
        json=payload,
    )

    assert first_link.status_code == 201
    assert second_link.status_code == 409


@pytest.mark.asyncio
async def test_link_customer_identity_returns_404_for_unknown_customer(client):
    response = await client.post(
        f"/api/v1/customers/{uuid4()}/identities",
        json={
            "source": "pipedrive",
            "entity_type": "organization",
            "external_id": str(uuid4()),
        },
    )

    assert response.status_code == 404
