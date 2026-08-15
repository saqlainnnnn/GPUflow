from apps.ai.core.llm import (
    LLMRequest,
    LLMResponse,
    LLMService,
)


class FakeLLMProvider:
    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        return LLMResponse(
            content='{"risk_score": 82}',
            model="fake-model",
            input_tokens=120,
            output_tokens=30,
        )


async def test_llm_service_calls_provider_with_prompt_version():
    provider = FakeLLMProvider()
    service = LLMService(provider)

    request = LLMRequest(
        system_prompt="You are a deal-risk analyst.",
        user_prompt="Analyze this deal.",
        prompt_version="deal_risk_v1",
    )

    response = await service.generate(request)

    assert response.content == '{"risk_score": 82}'
    assert response.model == "fake-model"
    assert response.input_tokens == 120
    assert response.output_tokens == 30


async def test_llm_request_requires_prompt_version():
    request = LLMRequest(
        system_prompt="system",
        user_prompt="user",
        prompt_version="deal_risk_v1",
    )

    assert request.prompt_version == "deal_risk_v1"


async def test_llm_response_calculates_total_tokens():
    response = LLMResponse(
        content="hello",
        model="fake-model",
        input_tokens=100,
        output_tokens=25,
    )

    assert response.total_tokens == 125
