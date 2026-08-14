from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.gpuaas.app.api.dependencies import get_db
from apps.gpuaas.app.main import app
from apps.gpuaas.app.models.customer import Customer


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
async def db_session():
    async for session in get_db():
        yield session


@pytest.mark.asyncio
async def test_create_customer(client):
    external_id = f"test_{uuid4()}"

    response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": external_id,
            "company_name": "Test AI",
            "email": "test@test.ai",
            "country": "us",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["external_id"] == external_id
    assert data["company_name"] == "Test AI"
    assert data["email"] == "test@test.ai"
    assert data["country"] == "US"
    assert data["status"] == "active"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_customer(client):
    external_id = f"test_{uuid4()}"

    create_response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": external_id,
            "company_name": "Get Test AI",
            "email": "get@test.ai",
            "country": "in",
        },
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/customers/{customer_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == customer_id
    assert data["external_id"] == external_id
    assert data["company_name"] == "Get Test AI"
    assert data["country"] == "IN"


@pytest.mark.asyncio
async def test_customer_not_found(client):
    customer_id = uuid4()

    response = await client.get(
        f"/api/v1/customers/{customer_id}"
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_external_id(client):
    external_id = f"duplicate_{uuid4()}"

    payload = {
        "external_id": external_id,
        "company_name": "Duplicate AI",
        "email": "duplicate@test.ai",
        "country": "us",
    }

    first_response = await client.post(
        "/api/v1/customers",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/customers",
        json=payload,
    )

    assert second_response.status_code == 409


@pytest.mark.asyncio
async def test_list_customers(client):
    external_id = f"list_{uuid4()}"

    create_response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": external_id,
            "company_name": "List Test AI",
            "email": "list@test.ai",
            "country": "us",
        },
    )

    assert create_response.status_code == 201

    response = await client.get(
        "/api/v1/customers"
    )

    assert response.status_code == 200

    customers = response.json()

    assert isinstance(customers, list)
    assert any(
        customer["external_id"] == external_id
        for customer in customers
    )
