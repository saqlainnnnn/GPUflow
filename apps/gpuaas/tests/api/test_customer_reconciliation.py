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


@pytest.mark.asyncio
async def test_reconcile_customer_source_persists_data_quality_record(
    client,
):
    from apps.gpuaas.app.repositories.customer_data_quality import (
        CustomerDataQualityRepository,
    )
    from apps.gpuaas.app.repositories.customer_identity import (
        CustomerIdentityRepository,
    )
    from apps.gpuaas.app.db.session import AsyncSessionLocal

    customer_external_id = (
        f"persisted_reconciliation_{uuid4()}"
    )

    create_response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": customer_external_id,
            "company_name": "Persisted Acme",
            "email": "hello@persisted-acme.ai",
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
                "company_name": "Persisted Acme",
                "email": "hello@persisted-acme.ai",
                "country": "IN",
            },
        },
    )

    assert response.status_code == 200

    async with AsyncSessionLocal() as session:
        repository = CustomerDataQualityRepository(
            session
        )

        record = await repository.find_for_identity(
            customer_id=customer_id,
            source="pipedrive",
            entity_type="organization",
            external_id=identity_external_id,
        )

        assert record is not None
        assert record.status == "matched"
        assert record.mismatches == []
        assert record.missing == []


@pytest.mark.asyncio
async def test_repeated_reconciliation_updates_existing_record(
    client,
):
    customer_external_id = (
        f"repeat_reconciliation_{uuid4()}"
    )

    create_response = await client.post(
        "/api/v1/customers",
        json={
            "external_id": customer_external_id,
            "company_name": "Repeat Acme",
            "email": "hello@repeat-acme.ai",
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

    first_response = await client.post(
        f"/api/v1/customers/{customer_id}/reconciliation",
        json={
            "source": "pipedrive",
            "entity_type": "organization",
            "external_id": identity_external_id,
            "source_record": {
                "company_name": "Repeat Acme",
                "email": "hello@repeat-acme.ai",
                "country": "IN",
            },
        },
    )

    assert first_response.status_code == 200
    assert first_response.json()["status"] == "matched"

    second_response = await client.post(
        f"/api/v1/customers/{customer_id}/reconciliation",
        json={
            "source": "pipedrive",
            "entity_type": "organization",
            "external_id": identity_external_id,
            "source_record": {
                "company_name": "Repeat Compute",
                "email": "hello@repeat-acme.ai",
                "country": "IN",
            },
        },
    )

    assert second_response.status_code == 200
    assert second_response.json()["status"] == "mismatch"
    assert second_response.json()["mismatches"] == [
        "company_name"
    ]

    from sqlalchemy import select

    from apps.gpuaas.app.db.session import AsyncSessionLocal
    from apps.gpuaas.app.models.customer_data_quality import (
        CustomerDataQualityRecord,
    )

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CustomerDataQualityRecord).where(
                CustomerDataQualityRecord.customer_id
                == customer_id,
                CustomerDataQualityRecord.source
                == "pipedrive",
                CustomerDataQualityRecord.entity_type
                == "organization",
                CustomerDataQualityRecord.external_id
                == identity_external_id,
            )
        )

        records = list(result.scalars().all())

    assert len(records) == 1

    assert records[0].status == "mismatch"
    assert records[0].mismatches == [
        "company_name"
    ]


@pytest.mark.asyncio
async def test_reconciliation_api_persists_ownership_classification(
    client,
):
    customer_external_id = (
        f"ownership_reconciliation_{uuid4()}"
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

    from sqlalchemy import select

    from apps.gpuaas.app.db.session import AsyncSessionLocal
    from apps.gpuaas.app.models.customer_data_quality import (
        CustomerDataQualityRecord,
    )

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CustomerDataQualityRecord).where(
                CustomerDataQualityRecord.customer_id
                == customer_id,
                CustomerDataQualityRecord.source
                == "pipedrive",
                CustomerDataQualityRecord.entity_type
                == "organization",
                CustomerDataQualityRecord.external_id
                == identity_external_id,
            )
        )

        record = result.scalar_one()

    assert (
        record.fields["company_name"]["classification"]
        == "authoritative_mismatch"
    )

    assert (
        record.fields["company_name"]["ownership"]
        == "authoritative"
    )
