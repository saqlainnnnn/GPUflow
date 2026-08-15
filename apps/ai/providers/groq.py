from typing import Any

from groq import AsyncGroq

from apps.ai.core.llm import (
    LLMRequest,
    LLMResponse,
)


class GroqProvider:
    def __init__(
        self,
        client: AsyncGroq,
        model: str,
    ) -> None:
        self.client = client
        self.model = model

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        response: Any = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": request.system_prompt,
                },
                {
                    "role": "user",
                    "content": request.user_prompt,
                },
            ],
        )

        content = response.choices[0].message.content

        if content is None:
            content = ""

        usage = response.usage

        input_tokens = 0
        output_tokens = 0

        if usage is not None:
            input_tokens = usage.prompt_tokens or 0
            output_tokens = usage.completion_tokens or 0

        return LLMResponse(
            content=content,
            model=response.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )


def build_groq_provider(
    api_key: str,
    model: str,
) -> GroqProvider:
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured",
        )

    client = AsyncGroq(
        api_key=api_key,
    )

    return GroqProvider(
        client=client,
        model=model,
    )