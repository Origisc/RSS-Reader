import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.llm import (
    HTTPChatCompletionsProvider,
    InMemoryProviderConfigStore,
    LLMProviderError,
    LLMRequest,
    ProviderConfig,
)
from mercury.ui.provider_presets import preset_by_id


def configured(
    *,
    base_url: str = "http://127.0.0.1:8080/v1",
    model: str = "user-selected-model",
    api_key: str = "local-test-secret",
    timeout_seconds: float = 45,
) -> ProviderConfig:
    return ProviderConfig(
        base_url=base_url,
        model=model,
        api_key=api_key,
        timeout_seconds=timeout_seconds,
    )


class RecordingTransport:
    def __init__(
        self,
        response: object | None = None,
        failure: Exception | None = None,
    ) -> None:
        self.response = response or {
            "choices": [
                {
                    "message": {
                        "content": "Fixed HTTP response",
                    }
                }
            ]
        }
        self.failure = failure
        self.calls: list[
            tuple[str, dict[str, str], dict[str, object], float]
        ] = []

    def __call__(
        self,
        url,
        headers,
        payload,
        timeout_seconds,
    ) -> object:
        self.calls.append(
            (
                url,
                dict(headers),
                dict(payload),
                timeout_seconds,
            )
        )
        if self.failure is not None:
            raise self.failure

        return self.response


class HTTPChatCompletionsProviderTest(unittest.TestCase):
    def test_supports_openai_and_gemini_compatible_endpoints(self) -> None:
        cases = (
            (
                "openai",
                "https://api.openai.com/v1",
                "openai-account-model",
                "https://api.openai.com/v1/chat/completions",
            ),
            (
                "gemini",
                (
                    "https://generativelanguage.googleapis.com/"
                    "v1beta/openai/"
                ),
                "gemini-account-model",
                (
                    "https://generativelanguage.googleapis.com/"
                    "v1beta/openai/chat/completions"
                ),
            ),
        )

        for provider_name, base_url, model, expected_url in cases:
            with self.subTest(provider=provider_name):
                transport = RecordingTransport()
                provider = HTTPChatCompletionsProvider(
                    InMemoryProviderConfigStore(
                        configured(
                            base_url=base_url,
                            model=model,
                            api_key="provider-test-secret",
                        )
                    ),
                    transport,
                )

                result = provider.test_connection()

                self.assertTrue(result.success)
                url, headers, payload, _timeout = transport.calls[0]
                self.assertEqual(url, expected_url)
                self.assertEqual(
                    headers["Authorization"],
                    "Bearer provider-test-secret",
                )
                self.assertEqual(payload["model"], model)
                self.assertEqual(payload["messages"][-1]["role"], "user")

    def test_local_deepseek_preset_builds_keyless_ollama_request(
        self,
    ) -> None:
        preset_config = preset_by_id(
            "ollama-local-deepseek"
        ).config
        assert preset_config is not None
        transport = RecordingTransport()
        provider = HTTPChatCompletionsProvider(
            InMemoryProviderConfigStore(preset_config),
            transport,
        )

        provider.complete(LLMRequest(prompt="Local-only fixture"))

        url, headers, payload, timeout = transport.calls[0]
        self.assertEqual(
            url,
            "http://127.0.0.1:11434/v1/chat/completions",
        )
        self.assertNotIn("Authorization", headers)
        self.assertEqual(payload["model"], "deepseek-r1:1.5b")
        self.assertEqual(timeout, 120.0)

    def test_builds_chat_request_from_user_configuration(self) -> None:
        transport = RecordingTransport()
        provider = HTTPChatCompletionsProvider(
            InMemoryProviderConfigStore(configured()),
            transport,
        )

        response = provider.complete(
            LLMRequest(
                prompt="Translate this paragraph.",
                system_prompt="Translate faithfully.",
                temperature=0,
            )
        )

        self.assertEqual(response.text, "Fixed HTTP response")
        self.assertEqual(len(transport.calls), 1)
        url, headers, payload, timeout = transport.calls[0]
        self.assertEqual(
            url,
            "http://127.0.0.1:8080/v1/chat/completions",
        )
        self.assertEqual(
            headers["Authorization"],
            "Bearer local-test-secret",
        )
        self.assertEqual(payload["model"], "user-selected-model")
        self.assertEqual(payload["temperature"], 0)
        self.assertEqual(
            payload["messages"],
            [
                {
                    "role": "system",
                    "content": "Translate faithfully.",
                },
                {
                    "role": "user",
                    "content": "Translate this paragraph.",
                },
            ],
        )
        self.assertEqual(timeout, 45)

    def test_reads_latest_saved_config_without_rebuilding_provider(
        self,
    ) -> None:
        store = InMemoryProviderConfigStore(configured())
        transport = RecordingTransport()
        provider = HTTPChatCompletionsProvider(store, transport)

        provider.complete(LLMRequest(prompt="First request"))
        store.save(
            configured(
                base_url="https://local.example/v2/chat/completions",
                model="second-model",
                api_key="",
                timeout_seconds=12,
            )
        )
        provider.complete(LLMRequest(prompt="Second request"))

        second_url, second_headers, second_payload, second_timeout = (
            transport.calls[1]
        )
        self.assertEqual(
            second_url,
            "https://local.example/v2/chat/completions",
        )
        self.assertNotIn("Authorization", second_headers)
        self.assertEqual(second_payload["model"], "second-model")
        self.assertEqual(second_timeout, 12)

    def test_unconfigured_provider_never_calls_transport(self) -> None:
        transport = RecordingTransport()
        provider = HTTPChatCompletionsProvider(
            InMemoryProviderConfigStore(),
            transport,
        )

        with self.assertRaises(LLMProviderError) as context:
            provider.complete(LLMRequest(prompt="Must stay local"))

        self.assertEqual(transport.calls, [])
        self.assertIn("not configured", str(context.exception))

    def test_connection_test_uses_unsaved_dialog_config(self) -> None:
        transport = RecordingTransport()
        provider = HTTPChatCompletionsProvider(
            InMemoryProviderConfigStore(),
            transport,
        )

        result = provider.test_config(configured(model="dialog-model"))

        self.assertTrue(result.success)
        self.assertIsNone(provider.config.model or None)
        self.assertEqual(
            transport.calls[0][2]["model"],
            "dialog-model",
        )
        messages = transport.calls[0][2]["messages"]
        self.assertEqual(messages[-1]["content"], "Reply with OK.")

    def test_timeout_is_safe_and_does_not_expose_api_key(self) -> None:
        secret = "do-not-render-this-secret"
        transport = RecordingTransport(
            failure=requests.Timeout(f"timeout using {secret}")
        )
        provider = HTTPChatCompletionsProvider(
            InMemoryProviderConfigStore(
                configured(api_key=secret)
            ),
            transport,
        )

        with self.assertRaises(LLMProviderError) as context:
            provider.complete(LLMRequest(prompt="Timeout fixture"))

        self.assertEqual(
            str(context.exception),
            "Provider request timed out.",
        )
        self.assertNotIn(secret, str(context.exception))

    def test_connection_test_preserves_safe_network_failure_category(
        self,
    ) -> None:
        cases = (
            (
                requests.exceptions.ProxyError("private proxy details"),
                "Provider proxy connection failed.",
            ),
            (
                requests.exceptions.SSLError(
                    "private certificate details"
                ),
                "Provider TLS certificate validation failed.",
            ),
            (
                requests.exceptions.ConnectionError(
                    "private DNS details"
                ),
                "Could not connect to Provider.",
            ),
        )

        for failure, expected in cases:
            with self.subTest(expected=expected):
                provider = HTTPChatCompletionsProvider(
                    InMemoryProviderConfigStore(),
                    RecordingTransport(failure=failure),
                )

                result = provider.test_config(configured())

                self.assertFalse(result.success)
                self.assertEqual(result.message, expected)
                self.assertNotIn("private", result.message)

    def test_rejects_malformed_response_without_backend_details(self) -> None:
        transport = RecordingTransport(
            response={"unexpected": "private backend details"}
        )
        provider = HTTPChatCompletionsProvider(
            InMemoryProviderConfigStore(configured()),
            transport,
        )

        with self.assertRaises(LLMProviderError) as context:
            provider.complete(LLMRequest(prompt="Malformed fixture"))

        self.assertEqual(
            str(context.exception),
            "Provider response did not contain choices.",
        )
        self.assertNotIn("private backend", str(context.exception))

    def test_supports_content_part_responses(self) -> None:
        transport = RecordingTransport(
            response={
                "choices": [
                    {
                        "message": {
                            "content": [
                                {"type": "text", "text": "Part one"},
                                {"type": "text", "text": " and two"},
                            ]
                        }
                    }
                ]
            }
        )
        provider = HTTPChatCompletionsProvider(
            InMemoryProviderConfigStore(configured()),
            transport,
        )

        response = provider.complete(LLMRequest(prompt="Parts fixture"))

        self.assertEqual(response.text, "Part one and two")

    def test_default_transport_posts_json_without_real_network(self) -> None:
        store = InMemoryProviderConfigStore(configured())
        provider = HTTPChatCompletionsProvider(store)

        with patch(
            "mercury.llm.http_provider.requests.post"
        ) as post:
            post.return_value.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "Patched network response",
                        }
                    }
                ]
            }

            response = provider.complete(
                LLMRequest(prompt="Patched request")
            )

        self.assertEqual(response.text, "Patched network response")
        post.return_value.raise_for_status.assert_called_once_with()
        post.assert_called_once()
        _args, kwargs = post.call_args
        self.assertEqual(
            kwargs["json"]["model"],
            "user-selected-model",
        )
        self.assertEqual(kwargs["timeout"], 45)

    def test_default_transport_maps_invalid_json_to_safe_error(self) -> None:
        provider = HTTPChatCompletionsProvider(
            InMemoryProviderConfigStore(configured())
        )

        with patch(
            "mercury.llm.http_provider.requests.post"
        ) as post:
            post.return_value.json.side_effect = ValueError(
                "private decoder details"
            )

            with self.assertRaises(LLMProviderError) as context:
                provider.complete(
                    LLMRequest(prompt="Invalid JSON fixture")
                )

        self.assertEqual(
            str(context.exception),
            "Provider returned invalid JSON.",
        )
        self.assertNotIn(
            "private decoder",
            str(context.exception),
        )


if __name__ == "__main__":
    unittest.main()
