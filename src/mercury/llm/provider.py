from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from mercury.llm.config import ProviderConfig


class LLMProviderError(RuntimeError):
    """A safe, user-readable Provider failure."""


@dataclass(frozen=True, slots=True)
class LLMRequest:
    prompt: str
    system_prompt: str = ""

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("Prompt cannot be empty.")


@dataclass(frozen=True, slots=True)
class LLMResponse:
    text: str


@dataclass(frozen=True, slots=True)
class ProviderConnectionResult:
    success: bool
    message: str


class LLMProvider(Protocol):
    """Unified interface used by every Mercury AI workflow."""

    @property
    def config(self) -> ProviderConfig:
        ...

    def complete(self, request: LLMRequest) -> LLMResponse:
        ...

    def test_connection(self) -> ProviderConnectionResult:
        ...


class MockLLMProvider:
    """Deterministic Provider with no file, network, or credential access."""

    def __init__(
        self,
        response_text: str = "Mock response",
        *,
        config: ProviderConfig | None = None,
        responder: Callable[[LLMRequest], str] | None = None,
        failure_message: str | None = None,
    ) -> None:
        self._config = config or ProviderConfig()
        self._response_text = response_text
        self._responder = responder
        self._failure_message = failure_message
        self._requests: list[LLMRequest] = []

    @property
    def config(self) -> ProviderConfig:
        return self._config

    @property
    def requests(self) -> tuple[LLMRequest, ...]:
        return tuple(self._requests)

    def complete(self, request: LLMRequest) -> LLMResponse:
        self._requests.append(request)

        if self._failure_message:
            raise LLMProviderError(self._failure_message)

        if self._responder is not None:
            return LLMResponse(text=self._responder(request))

        return LLMResponse(text=self._response_text)

    def test_connection(self) -> ProviderConnectionResult:
        if self._failure_message:
            return ProviderConnectionResult(
                success=False,
                message=self._failure_message,
            )

        return ProviderConnectionResult(
            success=True,
            message="Mock Provider is available.",
        )
