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

    response = await client.get(f"/api/v1/customers/{customer_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == customer_id
    assert data["external_id"] == external_id
    assert data["company_name"] == "Get Test AI"
    assert data["country"] == "IN"


@pytest.mark.asyncio
async def test_customer_not_found(client):
    customer_id = uuid4()

    response = await client.get(f"/api/v1/customers/{customer_id}")

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

    response = await client.get("/api/v1/customers")

    assert response.status_code == 200

    customers = response.json()

    assert isinstance(customers, list)
    assert any(customer["external_id"] == external_id for customer in customers)


@pytest.mark.asyncio
async def test_create_customer_flagged_by_kyb(
    client,
    monkeypatch,
):
    from apps.gpuaas.app.services.kyb import (
        KYBCheck,
        KYBDecision,
        KYBScreeningResult,
    )

    screening_result = KYBScreeningResult(
        decision=KYBDecision.FLAGGED,
        checks=[
            KYBCheck(
                check_type="denied_party",
                reason="Possible match",
                matched_value="Example Restricted Corp",
            )
        ],
    )

    class FakeKYB:
        def screen_customer(
            self,
            *,
            company_name,
            country,
        ):
            return screening_result

    monkeypatch.setattr(
        "apps.gpuaas.app.services.customer.KYBScreeningService",
        FakeKYB,
    )

    response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": f"kyb_flagged_{uuid4()}",
            "company_name": "Example Restricted Corp",
            "email": "flagged@test.ai",
            "country": "IN",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending_review"


@pytest.mark.asyncio
async def test_create_customer_blocked_by_kyb(
    client,
    monkeypatch,
):
    from apps.gpuaas.app.services.kyb import (
        KYBCheck,
        KYBDecision,
        KYBScreeningResult,
    )

    screening_result = KYBScreeningResult(
        decision=KYBDecision.BLOCKED,
        checks=[
            KYBCheck(
                check_type="restricted_country",
                reason="Restricted country",
                matched_value="XX",
            )
        ],
    )

    class FakeKYB:
        def screen_customer(
            self,
            *,
            company_name,
            country,
        ):
            return screening_result

    monkeypatch.setattr(
        "apps.gpuaas.app.services.customer.KYBScreeningService",
        FakeKYB,
    )

    response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": f"kyb_blocked_{uuid4()}",
            "company_name": "Blocked Customer",
            "email": "blocked@test.ai",
            "country": "IN",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "blocked"


@pytest.mark.asyncio
async def test_create_customer_persists_kyb_audit(
    client,
    db_session,
):
    external_id = f"kyb_audit_{uuid4()}"

    response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": external_id,
            "company_name": "Acme AI",
            "email": "audit@test.ai",
            "country": "IN",
        },
    )

    assert response.status_code == 201

    customer_id = response.json()["id"]

    from sqlalchemy import select

    from apps.gpuaas.app.models.kyb_audit import KYBAudit

    result = await db_session.execute(
        select(KYBAudit).where(
            KYBAudit.customer_id == customer_id
        )
    )

    audits = list(result.scalars().all())

    assert len(audits) == 1

    audit = audits[0]

    assert audit.check_type == "screening"
    assert audit.decision == "clear"
    assert audit.input_snapshot == {
        "company_name": "Acme AI",
        "country": "IN",
    }
    assert audit.reviewer is None


@pytest.mark.asyncio
async def test_kyb_review_approves_pending_customer(client):
    external_id = f"kyb_review_{uuid4()}"

    create_response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": external_id,
            "company_name": "Example Restricted Corp",
            "email": "review@test.ai",
            "country": "IN",
        },
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    assert create_response.json()["status"] == "pending_review"

    response = await client.post(
        f"/api/v1/customers/{customer_id}/kyb/review",
        json={
            "decision": "approve",
            "reviewer": "compliance@example.com",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == customer_id
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_kyb_review_rejects_pending_customer(client):
    external_id = f"kyb_reject_{uuid4()}"

    create_response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": external_id,
            "company_name": "Example Restricted Corp",
            "email": "reject@test.ai",
            "country": "IN",
        },
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    assert create_response.json()["status"] == "pending_review"

    response = await client.post(
        f"/api/v1/customers/{customer_id}/kyb/review",
        json={
            "decision": "reject",
            "reviewer": "compliance@example.com",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == customer_id
    assert data["status"] == "blocked"


@pytest.mark.asyncio
async def test_kyb_review_rejects_non_pending_customer(client):
    external_id = f"kyb_review_invalid_{uuid4()}"

    create_response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": external_id,
            "company_name": "Acme AI",
            "email": "clear@test.ai",
            "country": "IN",
        },
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/customers/{customer_id}/kyb/review",
        json={
            "decision": "approve",
            "reviewer": "compliance@example.com",
        },
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_kyb_review_persists_human_reviewer_audit(
    client,
    db_session,
):
    external_id = f"kyb_review_audit_{uuid4()}"

    create_response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": external_id,
            "company_name": "Example Restricted Corp",
            "email": "review-audit@test.ai",
            "country": "IN",
        },
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    assert create_response.json()["status"] == "pending_review"

    review_response = await client.post(
        f"/api/v1/customers/{customer_id}/kyb/review",
        json={
            "decision": "approve",
            "reviewer": "compliance@example.com",
        },
    )

    assert review_response.status_code == 200
    assert review_response.json()["status"] == "active"

    from uuid import UUID

    from sqlalchemy import select

    from apps.gpuaas.app.models.kyb_audit import KYBAudit

    result = await db_session.execute(
        select(KYBAudit).where(
            KYBAudit.customer_id == UUID(customer_id),
            KYBAudit.check_type == "human_review",
        )
    )

    audit = result.scalar_one()

    assert audit.decision == "approved"
    assert audit.reviewer == "compliance@example.com"
    assert audit.input_snapshot["previous_status"] == (
        "pending_review"
    )
