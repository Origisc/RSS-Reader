from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Any, Optional
from urllib import request, error
import json
import ssl


@dataclass
class LLMResult:
    success: bool
    content: str = ""
    error_message: Optional[str] = None


class LLMProvider(Protocol):
    def chat(self, messages: list[dict[str, str]], **kwargs) -> LLMResult:
        ...

    def get_name(self) -> str:
        ...


class MockProvider:
    def __init__(self, mock_response: str = ""):
        self._mock_response = mock_response or (
            "This is a mock translation response. "
            "In a real implementation, this would be replaced by the actual LLM output."
        )

    def chat(self, messages: list[dict[str, str]], **kwargs) -> LLMResult:
        return LLMResult(success=True, content=self._mock_response)

    def get_name(self) -> str:
        return "MockProvider"


class OpenAICompatibleProvider:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        timeout: int = 15,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def chat(self, messages: list[dict[str, str]], **kwargs) -> LLMResult:
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }

        try:
            context = ssl.create_default_context()
            req = request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

            with request.urlopen(req, timeout=self._timeout, context=context) as response:
                data = json.loads(response.read().decode("utf-8"))
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"].get("content", "")
                    return LLMResult(success=True, content=content)
                return LLMResult(success=False, error_message="No response from LLM")

        except error.HTTPError as e:
            return LLMResult(success=False, error_message=f"HTTP error: {e.code} - {e.reason}")
        except error.URLError as e:
            return LLMResult(success=False, error_message=f"Connection error: {str(e.reason)}")
        except json.JSONDecodeError:
            return LLMResult(success=False, error_message="Invalid response format")
        except TimeoutError:
            return LLMResult(success=False, error_message="Request timeout")
        except Exception as e:
            return LLMResult(success=False, error_message=f"Unexpected error: {str(e)}")

    def get_name(self) -> str:
        return "OpenAICompatibleProvider"


def create_provider(config: dict[str, Any]) -> LLMProvider:
    provider_type = config.get("type", "mock")

    if provider_type == "openai":
        return OpenAICompatibleProvider(
            base_url=config.get("base_url", ""),
            api_key=config.get("api_key", ""),
            model=config.get("model", "gpt-3.5-turbo"),
            timeout=config.get("timeout", 15),
        )

    return MockProvider(config.get("mock_response", ""))