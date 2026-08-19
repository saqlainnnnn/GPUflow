from unittest.mock import AsyncMock

import pytest

from apps.gpuaas.app.services.customer_orphan_scan import (
    CustomerOrphanScanService,
)


@pytest.mark.asyncio
async def test_scan_all_sources_combines_results():
    pipedrive_scanner = AsyncMock()
    xero_scanner = AsyncMock()

    pipedrive_scanner.scan.return_value = [
        "pipedrive-issue-1",
        "pipedrive-issue-2",
    ]

    xero_scanner.scan.return_value = [
        "xero-issue-1",
    ]

    service = CustomerOrphanScanService(
        pipedrive_scanner=pipedrive_scanner,
        xero_scanner=xero_scanner,
    )

    result = await service.scan_all()

    assert result == [
        "pipedrive-issue-1",
        "pipedrive-issue-2",
        "xero-issue-1",
    ]

    pipedrive_scanner.scan.assert_awaited_once()
    xero_scanner.scan.assert_awaited_once()


@pytest.mark.asyncio
async def test_scan_all_sources_returns_empty_when_no_issues():
    pipedrive_scanner = AsyncMock()
    xero_scanner = AsyncMock()

    pipedrive_scanner.scan.return_value = []
    xero_scanner.scan.return_value = []

    service = CustomerOrphanScanService(
        pipedrive_scanner=pipedrive_scanner,
        xero_scanner=xero_scanner,
    )

    result = await service.scan_all()

    assert result == []


@pytest.mark.asyncio
async def test_scan_all_sources_does_not_skip_xero_when_pipedrive_has_no_issues():
    pipedrive_scanner = AsyncMock()
    xero_scanner = AsyncMock()

    pipedrive_scanner.scan.return_value = []
    xero_scanner.scan.return_value = [
        "xero-issue-1",
    ]

    service = CustomerOrphanScanService(
        pipedrive_scanner=pipedrive_scanner,
        xero_scanner=xero_scanner,
    )

    result = await service.scan_all()

    assert result == ["xero-issue-1"]

    pipedrive_scanner.scan.assert_awaited_once()
    xero_scanner.scan.assert_awaited_once()
