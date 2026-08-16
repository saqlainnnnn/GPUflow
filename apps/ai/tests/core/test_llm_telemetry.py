from unittest.mock import AsyncMock

import pytest

from apps.ai.core.llm import (
    LLMRequest,
    LLMResponse,
    LLMService,
)


class FakeClock:
    def __init__(self):
        self.current = 100.0

    def time(self) -> float:
        self.current += 0.25
        return self.current


@pytest.mark.asyncio
async def test_llm_service_records_successful_invocation():
    provider = AsyncMock()

    provider.generate.return_value = LLMResponse(
        content="hello",
        model="llama-3.3-70b-versatile",
        input_tokens=100,
        output_tokens=25,
    )

    telemetry = AsyncMock()
    clock = FakeClock()

    service = LLMService(
        provider,
        telemetry=telemetry,
        clock=clock,
    )

    request = LLMRequest(
        system_prompt="system",
        user_prompt="user",
        prompt_version="deal_risk_v1",
    )

    result = await service.generate(request)

    assert result.content == "hello"

    telemetry.record.assert_awaited_once()

    event = telemetry.record.call_args.kwargs

    assert event["model"] == "llama-3.3-70b-versatile"
    assert event["prompt_version"] == "deal_risk_v1"
    assert event["input_tokens"] == 100
    assert event["output_tokens"] == 25
    assert event["total_tokens"] == 125
    assert event["latency_ms"] == 250.0
    assert event["success"] is True
    assert event["error"] is None


@pytest.mark.asyncio
async def test_llm_service_records_failed_invocation():
    provider = AsyncMock()

    provider.generate.side_effect = RuntimeError(
        "provider unavailable",
    )

    telemetry = AsyncMock()
    clock = FakeClock()

    service = LLMService(
        provider,
        telemetry=telemetry,
        clock=clock,
    )

    request = LLMRequest(
        system_prompt="system",
        user_prompt="user",
        prompt_version="deal_risk_v1",
    )

    with pytest.raises(RuntimeError):
        await service.generate(request)

    telemetry.record.assert_awaited_once()

    event = telemetry.record.call_args.kwargs

    assert event["prompt_version"] == "deal_risk_v1"
    assert event["success"] is False
    assert event["error"] == "provider unavailable"


@pytest.mark.asyncio
async def test_telemetry_is_optional():
    provider = AsyncMock()

    provider.generate.return_value = LLMResponse(
        content="hello",
        model="test-model",
        input_tokens=1,
        output_tokens=2,
    )

    service = LLMService(provider)

    result = await service.generate(
        LLMRequest(
            system_prompt="system",
            user_prompt="user",
            prompt_version="test_v1",
        )
    )

    assert result.content == "hello"
