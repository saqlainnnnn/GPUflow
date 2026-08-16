import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace

from apps.ai.core.llm import (
    LLMRequest,
    LLMResponse,
)
from apps.ai.providers.groq import GroqProvider


@pytest.mark.asyncio
async def test_groq_provider_maps_request_and_response():
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=AsyncMock(
                    return_value=SimpleNamespace(
                        model="llama-3.3-70b-versatile",
                        choices=[
                            SimpleNamespace(
                                message=SimpleNamespace(
                                    content='{"risk_score": 82}',
                                )
                            )
                        ],
                        usage=SimpleNamespace(
                            prompt_tokens=120,
                            completion_tokens=30,
                        ),
                    )
                )
            )
        )
    )

    provider = GroqProvider(
        client=client,
        model="llama-3.3-70b-versatile",
    )

    request = LLMRequest(
        system_prompt="You are a deal-risk analyst.",
        user_prompt="Analyze this deal.",
        prompt_version="deal_risk_v1",
    )

    result = await provider.generate(request)

    assert isinstance(result, LLMResponse)
    assert result.content == '{"risk_score": 82}'
    assert result.model == "llama-3.3-70b-versatile"
    assert result.input_tokens == 120
    assert result.output_tokens == 30

    client.chat.completions.create.assert_awaited_once_with(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a deal-risk analyst.",
            },
            {
                "role": "user",
                "content": "Analyze this deal.",
            },
        ],
        response_format={
            "type": "json_object",
        },
    )


@pytest.mark.asyncio
async def test_groq_provider_handles_missing_usage():
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=AsyncMock(
                    return_value=SimpleNamespace(
                        model="test-model",
                        choices=[
                            SimpleNamespace(
                                message=SimpleNamespace(
                                    content="{}",
                                )
                            )
                        ],
                        usage=None,
                    )
                )
            )
        )
    )

    provider = GroqProvider(
        client=client,
        model="test-model",
    )

    result = await provider.generate(
        LLMRequest(
            system_prompt="system",
            user_prompt="user",
            prompt_version="test_v1",
        )
    )

    assert result.input_tokens == 0
    assert result.output_tokens == 0