from typing import Any, Protocol

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


class PipedriveClientProtocol(Protocol):
    async def get_organization(
        self,
        organization_id: int,
    ) -> dict[str, Any]: ...

    async def get_deal(
        self,
        deal_id: int,
    ) -> dict[str, Any]: ...

    async def get_deal_changelog(
        self,
        *,
        deal_id: int,
    ) -> list[dict[str, Any]]: ...

    async def get_activities(
        self,
        *,
        deal_id: int,
    ) -> list[dict[str, Any]]: ...


class CRMOrganizationNotFoundError(Exception):
    pass


class CRMDealNotFoundError(Exception):
    pass


class CRMDealChangelogNotFoundError(Exception):
    pass


class CRMActivitiesNotFoundError(Exception):
    pass


class CRMTool:
    def __init__(
        self,
        pipedrive_client: PipedriveClientProtocol,
    ) -> None:
        self.pipedrive_client = pipedrive_client

    async def get_organization(
        self,
        data: GetOrganizationInput,
    ) -> OrganizationToolOutput:
        try:
            organization = await self.pipedrive_client.get_organization(
                data.organization_id,
            )
        except ValueError as exc:
            raise CRMOrganizationNotFoundError(
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

        return OrganizationToolOutput(
            id=organization_id,
            name=name,
            address=organization.get("address"),
            owner_id=organization.get("owner_id"),
        )

    async def get_deal(
        self,
        data: GetDealInput,
    ) -> DealToolOutput:
        try:
            deal = await self.pipedrive_client.get_deal(
                data.deal_id,
            )
        except ValueError as exc:
            raise CRMDealNotFoundError(
                f"Deal '{data.deal_id}' not found",
            ) from exc

        deal_id = deal.get("id")

        if deal_id is None:
            raise ValueError(
                "Pipedrive deal response missing id",
            )

        title = deal.get("title")

        if not title:
            raise ValueError(
                "Pipedrive deal response missing title",
            )

        status = deal.get("status")

        if not status:
            raise ValueError(
                "Pipedrive deal response missing status",
            )

        return DealToolOutput(
            id=deal_id,
            title=title,
            value=deal.get("value"),
            currency=deal.get("currency"),
            status=status,
            stage_id=deal.get("stage_id"),
            organization_id=deal.get("org_id"),
            owner_id=deal.get("owner_id"),
            created_at=deal.get("add_time"),
            updated_at=deal.get("update_time"),
        )

    async def get_deal_changelog(
        self,
        data: GetDealChangelogInput,
    ) -> list[DealChangelogToolOutput]:
        try:
            changes = await self.pipedrive_client.get_deal_changelog(
                deal_id=data.deal_id,
            )
        except ValueError as exc:
            raise CRMDealChangelogNotFoundError(
                f"Deal changelog for '{data.deal_id}' not found",
            ) from exc

        results: list[DealChangelogToolOutput] = []

        for change in changes:
            field_key = change.get("field_key")
            timestamp = change.get("timestamp")

            if not field_key:
                raise ValueError(
                    "Pipedrive deal changelog response missing field_key",
                )

            if not timestamp:
                raise ValueError(
                    "Pipedrive deal changelog response missing timestamp",
                )

            results.append(
                DealChangelogToolOutput(
                    field_key=field_key,
                    old_value=change.get("old_value"),
                    new_value=change.get("new_value"),
                    timestamp=timestamp,
                )
            )

        return results

    async def get_activities(
        self,
        data: GetActivitiesInput,
    ) -> list[ActivityToolOutput]:
        try:
            activities = await self.pipedrive_client.get_activities(
                deal_id=data.deal_id,
            )
        except ValueError as exc:
            raise CRMActivitiesNotFoundError(
                f"Activities for deal '{data.deal_id}' not found",
            ) from exc

        outputs: list[ActivityToolOutput] = []

        for activity in activities:
            activity_id = activity.get("id")

            if activity_id is None:
                raise ValueError(
                    "Pipedrive activity response missing id",
                )

            subject = activity.get("subject")

            if not subject:
                raise ValueError(
                    "Pipedrive activity response missing subject",
                )

            activity_type = activity.get("type")

            if not activity_type:
                raise ValueError(
                    "Pipedrive activity response missing type",
                )

            status = activity.get("status")

            if not status:
                raise ValueError(
                    "Pipedrive activity response missing status",
                )

            outputs.append(
                ActivityToolOutput(
                    activity_id=activity_id,
                    subject=subject,
                    type=activity_type,
                    status=status,
                    due_date=activity.get("due_date"),
                    done=activity.get("done"),
                    owner_id=activity.get("owner_id"),
                    deal_id=activity.get("deal_id"),
                    organization_id=activity.get("org_id"),
                    person_id=activity.get("person_id"),
                    updated_at=activity.get("update_time"),
                )
            )

        return outputs
