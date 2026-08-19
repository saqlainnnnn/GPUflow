from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.integration_hub.app.repositories.event import EventRepository



@pytest.mark.asyncio
async def test_get_oldest_unprocessed():
    session = AsyncMock()
    repository = EventRepository(session)

    event = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = event
    session.execute.return_value = result

    assert await repository.get_oldest_unprocessed() is event
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_processed_events():
    session = AsyncMock()
    repository = EventRepository(session)

    events = [MagicMock(), MagicMock()]
    result = MagicMock()
    result.scalars.return_value.all.return_value = events
    session.execute.return_value = result

    assert await repository.get_processed_events() == events


@pytest.mark.asyncio
async def test_get_all_events():
    session = AsyncMock()
    repository = EventRepository(session)

    events = [MagicMock()]
    result = MagicMock()
    result.scalars.return_value.all.return_value = events
    session.execute.return_value = result

    assert await repository.get_all_events() == events
