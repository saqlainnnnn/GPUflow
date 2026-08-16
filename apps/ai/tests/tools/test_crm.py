from unittest.mock import AsyncMock

import pytest

from apps.ai.tools.crm import (
    CRMActivitiesNotFoundError,
    CRMDealNotFoundError,
    CRMOrganizationNotFoundError,
    CRMTool,
)
from apps.ai.tools.schemas import (
    ActivityToolOutput,
    DealChangelogToolOutput,
    DealToolOutput,
    GetActivitiesInput,
    GetDealChangelogInput,
    GetDealInput,
    GetOrganizationInput,
    OrganizationToolOutput,
)


@pytest.fixture
def pipedrive_client():
    return AsyncMock()


@pytest.fixture
def crm_tool(pipedrive_client):
    return CRMTool(pipedrive_client)


@pytest.mark.asyncio
async def test_get_organization_returns_structured_output(
    crm_tool,
    pipedrive_client,
):
    pipedrive_client.get_organization.return_value = {
        "id": 123,
        "name": "Acme AI",
        "address": "Hyderabad, India",
        "owner_id": 42,
    }

    result = await crm_tool.get_organization(
        GetOrganizationInput(
            organization_id=123,
        )
    )

    assert isinstance(result, OrganizationToolOutput)
    assert result.id == 123
    assert result.name == "Acme AI"
    assert result.address == "Hyderabad, India"
    assert result.owner_id == 42

    pipedrive_client.get_organization.assert_awaited_once_with(123)


@pytest.mark.asyncio
async def test_get_organization_allows_missing_optional_fields(
    crm_tool,
    pipedrive_client,
):
    pipedrive_client.get_organization.return_value = {
        "id": 123,
        "name": "Acme AI",
    }

    result = await crm_tool.get_organization(
        GetOrganizationInput(
            organization_id=123,
        )
    )

    assert result.id == 123
    assert result.name == "Acme AI"
    assert result.address is None
    assert result.owner_id is None


@pytest.mark.asyncio
async def test_get_organization_translates_missing_organization(
    crm_tool,
    pipedrive_client,
):
    pipedrive_client.get_organization.side_effect = ValueError(
        "Organization not found",
    )

    with pytest.raises(CRMOrganizationNotFoundError):
        await crm_tool.get_organization(
            GetOrganizationInput(
                organization_id=999,
            )
        )


def test_get_organization_input_rejects_invalid_id():
    with pytest.raises(ValueError):
        GetOrganizationInput(
            organization_id="not-an-int",
        )


@pytest.mark.asyncio
async def test_get_deal_returns_structured_output(
    crm_tool,
    pipedrive_client,
):
    pipedrive_client.get_deal.return_value = {
        "id": 456,
        "title": "Acme H100 Expansion",
        "value": 125000,
        "currency": "USD",
        "status": "open",
        "stage_id": 7,
        "org_id": 123,
        "owner_id": 42,
    }

    result = await crm_tool.get_deal(
        GetDealInput(
            deal_id=456,
        )
    )

    assert isinstance(result, DealToolOutput)
    assert result.id == 456
    assert result.title == "Acme H100 Expansion"
    assert result.value == 125000
    assert result.currency == "USD"
    assert result.status == "open"
    assert result.stage_id == 7
    assert result.organization_id == 123
    assert result.owner_id == 42

    pipedrive_client.get_deal.assert_awaited_once_with(456)


@pytest.mark.asyncio
async def test_get_deal_allows_missing_optional_fields(
    crm_tool,
    pipedrive_client,
):
    pipedrive_client.get_deal.return_value = {
        "id": 456,
        "title": "Acme H100 Expansion",
        "status": "open",
    }

    result = await crm_tool.get_deal(
        GetDealInput(
            deal_id=456,
        )
    )

    assert result.id == 456
    assert result.title == "Acme H100 Expansion"
    assert result.value is None
    assert result.currency is None
    assert result.stage_id is None
    assert result.organization_id is None
    assert result.owner_id is None


@pytest.mark.asyncio
async def test_get_deal_translates_missing_deal(
    crm_tool,
    pipedrive_client,
):
    pipedrive_client.get_deal.side_effect = ValueError(
        "Deal not found",
    )

    with pytest.raises(CRMDealNotFoundError):
        await crm_tool.get_deal(
            GetDealInput(
                deal_id=999,
            )
        )


def test_get_deal_input_rejects_invalid_id():
    with pytest.raises(ValueError):
        GetDealInput(
            deal_id="not-an-int",
        )


@pytest.mark.asyncio
async def test_get_activities_returns_structured_output(
    crm_tool,
    pipedrive_client,
):
    pipedrive_client.get_activities.return_value = [
        {
            "id": 1001,
            "subject": "Follow up on GPU requirements",
            "type": "call",
            "status": "done",
            "due_date": "2026-08-14",
            "done": True,
            "owner_id": 42,
            "deal_id": 456,
            "org_id": 123,
            "person_id": 789,
        },
        {
            "id": 1002,
            "subject": "Send H100 pricing",
            "type": "task",
            "status": "planned",
            "due_date": "2026-08-20",
            "done": False,
            "owner_id": 42,
            "deal_id": 456,
            "org_id": 123,
            "person_id": 789,
        },
    ]

    result = await crm_tool.get_activities(
        GetActivitiesInput(
            deal_id=456,
        )
    )

    assert len(result) == 2

    assert isinstance(result[0], ActivityToolOutput)
    assert result[0].activity_id == 1001
    assert result[0].subject == "Follow up on GPU requirements"
    assert result[0].type == "call"
    assert result[0].status == "done"
    assert result[0].due_date == "2026-08-14"
    assert result[0].done is True
    assert result[0].owner_id == 42
    assert result[0].deal_id == 456
    assert result[0].organization_id == 123
    assert result[0].person_id == 789

    pipedrive_client.get_activities.assert_awaited_once_with(
        deal_id=456,
    )


@pytest.mark.asyncio
async def test_get_activities_allows_missing_optional_fields(
    crm_tool,
    pipedrive_client,
):
    pipedrive_client.get_activities.return_value = [
        {
            "id": 1001,
            "subject": "Follow up",
            "type": "call",
            "status": "done",
        },
    ]

    result = await crm_tool.get_activities(
        GetActivitiesInput(
            deal_id=456,
        )
    )

    assert len(result) == 1
    assert result[0].activity_id == 1001
    assert result[0].subject == "Follow up"
    assert result[0].due_date is None
    assert result[0].done is None
    assert result[0].owner_id is None
    assert result[0].deal_id is None
    assert result[0].organization_id is None
    assert result[0].person_id is None


@pytest.mark.asyncio
async def test_get_activities_translates_missing_deal(
    crm_tool,
    pipedrive_client,
):
    pipedrive_client.get_activities.side_effect = ValueError(
        "Deal not found",
    )

    with pytest.raises(CRMActivitiesNotFoundError):
        await crm_tool.get_activities(
            GetActivitiesInput(
                deal_id=999,
            )
        )


def test_get_activities_input_rejects_invalid_id():
    with pytest.raises(ValueError):
        GetActivitiesInput(
            deal_id="not-an-int",
        )


@pytest.mark.asyncio
async def test_get_deal_includes_created_and_updated_timestamps(
    crm_tool,
    pipedrive_client,
):
    pipedrive_client.get_deal.return_value = {
        "id": 456,
        "title": "Acme H100 Expansion",
        "value": 125000,
        "currency": "USD",
        "status": "open",
        "stage_id": 7,
        "org_id": 123,
        "owner_id": 42,
        "add_time": "2026-06-01 10:30:00",
        "update_time": "2026-08-15 14:00:00",
    }

    result = await crm_tool.get_deal(
        GetDealInput(deal_id=456),
    )

    assert result.created_at == "2026-06-01 10:30:00"
    assert result.updated_at == "2026-08-15 14:00:00"
    assert result.stage_id == 7


@pytest.mark.asyncio
async def test_get_deal_changelog_returns_structured_history(
    crm_tool,
    pipedrive_client,
):
    pipedrive_client.get_deal_changelog.return_value = [
        {
            "field_key": "stage_id",
            "old_value": 5,
            "new_value": 7,
            "timestamp": "2026-07-01 12:00:00",
        },
        {
            "field_key": "stage_id",
            "old_value": 4,
            "new_value": 5,
            "timestamp": "2026-06-20 09:00:00",
        },
    ]

    result = await crm_tool.get_deal_changelog(
        GetDealChangelogInput(deal_id=456),
    )

    assert len(result) == 2

    assert isinstance(result[0], DealChangelogToolOutput)
    assert result[0].field_key == "stage_id"
    assert result[0].old_value == 5
    assert result[0].new_value == 7
    assert result[0].timestamp == "2026-07-01 12:00:00"

    pipedrive_client.get_deal_changelog.assert_awaited_once_with(
        deal_id=456,
    )


def test_get_deal_changelog_input_rejects_invalid_id():
    with pytest.raises(ValueError):
        GetDealChangelogInput(
            deal_id="not-an-int",
        )
