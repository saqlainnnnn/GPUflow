from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.gpuaas.app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_reconcile_customer_source(
    client,
):
    customer_external_id = (
        f"reconciliation_{uuid4()}"
    )

    create_response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": customer_external_id,
            "company_name": "Acme AI",
            "email": "hello@acme.ai",
            "country": "IN",
        },
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    identity_external_id = str(uuid4())

    identity_response = await client.post(
        f"/api/v1/customers/{customer_id}/identities",
        json={
            "source": "pipedrive",
            "entity_type": "organization",
            "external_id": identity_external_id,
        },
    )

    assert identity_response.status_code == 201

    response = await client.post(
        f"/api/v1/customers/{customer_id}/reconciliation",
        json={
            "source": "pipedrive",
            "entity_type": "organization",
            "external_id": identity_external_id,
            "source_record": {
                "company_name": "  ACME AI ",
                "email": "HELLO@ACME.AI",
                "country": "in",
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["source"] == "pipedrive"
    assert data["entity_type"] == "organization"
    assert data["status"] == "matched"
    assert data["mismatches"] == []
    assert data["missing"] == []


@pytest.mark.asyncio
async def test_reconcile_customer_source_returns_mismatch(
    client,
):
    customer_external_id = (
        f"reconciliation_mismatch_{uuid4()}"
    )

    create_response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": customer_external_id,
            "company_name": "Acme AI",
            "email": "hello@acme.ai",
            "country": "IN",
        },
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    identity_external_id = str(uuid4())

    identity_response = await client.post(
        f"/api/v1/customers/{customer_id}/identities",
        json={
            "source": "pipedrive",
            "entity_type": "organization",
            "external_id": identity_external_id,
        },
    )

    assert identity_response.status_code == 201

    response = await client.post(
        f"/api/v1/customers/{customer_id}/reconciliation",
        json={
            "source": "pipedrive",
            "entity_type": "organization",
            "external_id": identity_external_id,
            "source_record": {
                "company_name": "Acme Compute",
                "email": "hello@acme.ai",
                "country": "IN",
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "mismatch"
    assert data["mismatches"] == ["company_name"]


@pytest.mark.asyncio
async def test_reconcile_customer_source_rejects_unlinked_identity(
    client,
):
    create_response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": f"unlinked_{uuid4()}",
            "company_name": "Unlinked AI",
            "email": "hello@unlinked.ai",
            "country": "IN",
        },
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/customers/{customer_id}/reconciliation",
        json={
            "source": "pipedrive",
            "entity_type": "organization",
            "external_id": str(uuid4()),
            "source_record": {
                "company_name": "Unlinked AI",
                "email": "hello@unlinked.ai",
                "country": "IN",
            },
        },
    )

    assert response.status_code == 409
