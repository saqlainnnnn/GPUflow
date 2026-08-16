from unittest.mock import AsyncMock

import pytest

from apps.ai.tools.pipedrive import (
    PipedriveOrganizationNotFoundToolError,
    PipedriveTool,
)
from apps.ai.tools.schemas import (
    PipedriveOrganizationToolOutput,
    UpdatePipedriveOrganizationInput,
)


@pytest.fixture
def pipedrive_client():
    client = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_update_pipedrive_organization_returns_structured_output(
    pipedrive_client,
):
    pipedrive_client.update_organization.return_value = {
        "id": 123,
        "name": "Acme AI Updated",
        "address": "123 Market Street",
        "owner_id": 42,
    }

    tool = PipedriveTool(pipedrive_client)

    result = await tool.update_organization(
        UpdatePipedriveOrganizationInput(
            organization_id=123,
            name="Acme AI Updated",
            address="123 Market Street",
        )
    )

    assert isinstance(result, PipedriveOrganizationToolOutput)
    assert result.id == 123
    assert result.name == "Acme AI Updated"
    assert result.address == "123 Market Street"
    assert result.owner_id == 42

    pipedrive_client.update_organization.assert_awaited_once_with(
        123,
        name="Acme AI Updated",
        address="123 Market Street",
    )


def test_update_pipedrive_organization_requires_at_least_one_field():
    with pytest.raises(ValueError):
        UpdatePipedriveOrganizationInput(
            organization_id=123,
        )


@pytest.mark.asyncio
async def test_update_pipedrive_organization_translates_missing_organization(
    pipedrive_client,
):
    pipedrive_client.update_organization.side_effect = ValueError(
        "Organization not found",
    )

    tool = PipedriveTool(pipedrive_client)

    with pytest.raises(PipedriveOrganizationNotFoundToolError):
        await tool.update_organization(
            UpdatePipedriveOrganizationInput(
                organization_id=123,
                name="Acme AI",
            )
        )
