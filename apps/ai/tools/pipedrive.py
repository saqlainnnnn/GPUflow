from typing import Any, Protocol

from apps.ai.tools.schemas import (
    PipedriveOrganizationToolOutput,
    UpdatePipedriveOrganizationInput,
)


class PipedriveClientProtocol(Protocol):
    async def update_organization(
        self,
        organization_id: int,
        *,
        name: str | None = None,
        address: str | None = None,
    ) -> dict[str, Any]: ...


class PipedriveOrganizationNotFoundToolError(Exception):
    pass


class PipedriveTool:
    def __init__(
        self,
        pipedrive_client: PipedriveClientProtocol,
    ) -> None:
        self.pipedrive_client = pipedrive_client

    async def update_organization(
        self,
        data: UpdatePipedriveOrganizationInput,
    ) -> PipedriveOrganizationToolOutput:
        try:
            organization = await self.pipedrive_client.update_organization(
                data.organization_id,
                name=data.name,
                address=data.address,
            )
        except ValueError as exc:
            raise PipedriveOrganizationNotFoundToolError(
                f"Organization '{data.organization_id}' not found",
            ) from exc

        organization_id = organization.get("id")

        if organization_id is None:
            raise ValueError(
                "Pipedrive organization response missing id",
            )

        name = organization.get("name")

        if not name:
            raise ValueError(
                "Pipedrive organization response missing name",
            )

        return PipedriveOrganizationToolOutput(
            id=organization_id,
            name=name,
            address=organization.get("address"),
            owner_id=organization.get("owner_id"),
        )
