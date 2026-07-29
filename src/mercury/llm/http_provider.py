from collections.abc import Callable, Mapping
from typing import Any

import requests

from mercury.llm.config import (
    ProviderConfig,
    ProviderConfigError,
    ProviderConfigStore,
)
from mercury.llm.provider import (
    LLMProviderError,
    LLMRequest,
    LLMResponse,
    ProviderConnectionResult,
)


JSONTransport = Callable[
    [str, Mapping[str, str], Mapping[str, object], float],
    object,
]


class HTTPChatCompletionsProvider:
    """Provider-neutral adapter for configurable Chat Completions APIs."""

    def __init__(
        self,
        config_store: ProviderConfigStore,
        transport: JSONTransport | None = None,
    ) -> None:
        self._config_store = config_store
        self._transport = transport or self._post_json

    @property
    def config(self) -> ProviderConfig:
        try:
            return self._config_store.load() or ProviderConfig()
        except Exception:
            return ProviderConfig()

    def complete(self, request: LLMRequest) -> LLMResponse:
        return self._complete_with_config(request, self.config)

    def test_connection(self) -> ProviderConnectionResult:
        return self.test_config(self.config)

    def test_config(
        self,
        config: ProviderConfig,
    ) -> ProviderConnectionResult:
        try:
            response = self._complete_with_config(
                LLMRequest(
                    prompt="Reply with OK.",
                    system_prompt=(
                        "This is an explicit connection test. "
                        "Return only a short acknowledgement."
                    ),
                ),
                config,
            )
        except LLMProviderError as exc:
            return ProviderConnectionResult(False, str(exc))

        if not response.text.strip():
            return ProviderConnectionResult(
                False,
                "Provider returned an empty connection-test response.",
            )

        return ProviderConnectionResult(
            True,
            "Provider connection succeeded.",
        )

    def _complete_with_config(
        self,
        request: LLMRequest,
        config: ProviderConfig,
    ) -> LLMResponse:
        try:
            valid_config = config.require_valid()
        except ProviderConfigError as exc:
            raise LLMProviderError(
                "AI Provider is not configured correctly."
            ) from exc

        messages: list[dict[str, str]] = []
        if request.system_prompt.strip():
            messages.append(
                {
                    "role": "system",
                    "content": request.system_prompt,
                }
            )
        messages.append(
            {
                "role": "user",
                "content": request.prompt,
            }
        )
        payload: dict[str, object] = {
            "model": valid_config.model.strip(),
            "messages": messages,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if valid_config.api_key:
            headers["Authorization"] = (
                f"Bearer {valid_config.api_key}"
            )

        response_data = self._send(
            self._completion_url(valid_config.base_url),
            headers,
            payload,
            valid_config.timeout_seconds,
        )
        content = self._response_text(response_data)

        if not content.strip():
            raise LLMProviderError(
                "Provider returned an empty response."
            )

        return LLMResponse(text=content.strip())

    def _send(
        self,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
    ) -> object:
        try:
            return self._transport(
                url,
                headers,
                payload,
                timeout_seconds,
            )
        except (requests.Timeout, TimeoutError) as exc:
            raise LLMProviderError(
                "Provider request timed out."
            ) from exc
        except requests.exceptions.ProxyError as exc:
            raise LLMProviderError(
                "Provider proxy connection failed."
            ) from exc
        except requests.exceptions.SSLError as exc:
            raise LLMProviderError(
                "Provider TLS certificate validation failed."
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise LLMProviderError(
                "Could not connect to Provider."
            ) from exc
        except requests.exceptions.InvalidURL as exc:
            raise LLMProviderError(
                "Provider URL is invalid."
            ) from exc
        except ValueError as exc:
            raise LLMProviderError(
                "Provider returned invalid JSON."
            ) from exc
        except requests.HTTPError as exc:
            status_code = (
                exc.response.status_code
                if exc.response is not None
                else None
            )
            message = (
                f"Provider request failed with HTTP status {status_code}."
                if status_code is not None
                else "Provider request failed."
            )
            raise LLMProviderError(message) from exc
        except requests.RequestException as exc:
            raise LLMProviderError(
                "Provider request failed."
            ) from exc
        except LLMProviderError:
            raise
        except Exception as exc:
            raise LLMProviderError(
                "Provider request failed."
            ) from exc

    @staticmethod
    def _completion_url(base_url: str) -> str:
        normalized = base_url.strip().rstrip("/")

        if normalized.endswith("/chat/completions"):
            return normalized

        return f"{normalized}/chat/completions"

    @classmethod
    def _response_text(cls, response_data: object) -> str:
        if not isinstance(response_data, Mapping):
            raise LLMProviderError(
                "Provider returned an unexpected response."
            )

        choices = response_data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise LLMProviderError(
                "Provider response did not contain choices."
            )

        first_choice = choices[0]
        if not isinstance(first_choice, Mapping):
            raise LLMProviderError(
                "Provider returned an unexpected choice."
            )

        message = first_choice.get("message")
        if isinstance(message, Mapping):
            content = message.get("content")
            extracted = cls._content_text(content)
            if extracted:
                return extracted

        legacy_text = first_choice.get("text")
        if isinstance(legacy_text, str):
            return legacy_text

        raise LLMProviderError(
            "Provider response did not contain message content."
        )

    @staticmethod
    def _content_text(content: Any) -> str:
        if isinstance(content, str):
            return content

        if not isinstance(content, list):
            return ""

        parts: list[str] = []
        for item in content:
            if not isinstance(item, Mapping):
                continue

            text = item.get("text")
            if isinstance(text, str):
                parts.append(text)

        return "".join(parts)

    @staticmethod
    def _post_json(
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
    ) -> object:
        response = requests.post(
            url,
            headers=dict(headers),
            json=dict(payload),
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        return response.json()
