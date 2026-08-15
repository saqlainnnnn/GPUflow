from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMRequest:
    system_prompt: str
    user_prompt: str
    prompt_version: str


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class LLMProvider(Protocol):
    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse: ...


class LLMService:
    def __init__(
        self,
        provider: LLMProvider,
    ) -> None:
        self.provider = provider

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        return await self.provider.generate(request)
