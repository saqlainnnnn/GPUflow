from dataclasses import dataclass
from time import perf_counter
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


class LLMInvocationTelemetry(Protocol):
    async def record(
        self,
        *,
        model: str | None = None,
        prompt_version: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        latency_ms: float,
        success: bool,
        error: str | None = None,
    ) -> None: ...


class LLMService:
    def __init__(
        self,
        provider: LLMProvider,
        *,
        telemetry: LLMInvocationTelemetry | None = None,
        clock=perf_counter,
    ) -> None:
        self.provider = provider
        self.telemetry = telemetry
        self.clock = clock

    def _now(self) -> float:
        if callable(self.clock):
            return self.clock()

        return self.clock.time()

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        started = self._now()

        try:
            response = await self.provider.generate(
                request,
            )
        except Exception as exc:
            latency_ms = round(
                (self._now() - started) * 1000,
                2,
            )

            if self.telemetry is not None:
                await self.telemetry.record(
                    model=None,
                    prompt_version=request.prompt_version,
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    latency_ms=latency_ms,
                    success=False,
                    error=str(exc),
                )

            raise

        latency_ms = round(
            (self._now() - started) * 1000,
            2,
        )

        if self.telemetry is not None:
            await self.telemetry.record(
                model=response.model,
                prompt_version=request.prompt_version,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                total_tokens=response.total_tokens,
                latency_ms=latency_ms,
                success=True,
                error=None,
            )

        return response
