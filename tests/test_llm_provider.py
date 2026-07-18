import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.llm import (
    InMemoryProviderConfigStore,
    LLMProviderError,
    LLMRequest,
    MockLLMProvider,
    ProviderConfig,
    ProviderConfigError,
)


class ProviderConfigTest(unittest.TestCase):
    def test_valid_provider_neutral_configuration(self) -> None:
        config = ProviderConfig(
            base_url="http://127.0.0.1:8080/v1",
            model="user-selected-model",
            api_key="local-secret",
            timeout_seconds=45,
        )

        self.assertTrue(config.is_configured)
        self.assertTrue(config.has_api_key)
        self.assertIs(config.require_valid(), config)

    def test_configuration_reports_all_user_correctable_errors(self) -> None:
        config = ProviderConfig(
            base_url="not-a-url",
            model="",
            timeout_seconds=500,
        )

        with self.assertRaises(ProviderConfigError) as context:
            config.require_valid()

        message = str(context.exception)
        self.assertIn("Base URL", message)
        self.assertIn("Model name", message)
        self.assertIn("Timeout", message)

    def test_api_key_is_excluded_from_repr(self) -> None:
        secret = "must-not-appear-in-output"
        config = ProviderConfig(
            base_url="https://example.invalid/v1",
            model="test-model",
            api_key=secret,
        )

        self.assertNotIn(secret, repr(config))
        self.assertNotIn(secret, str(config))

    def test_in_memory_store_can_save_load_and_clear(self) -> None:
        store = InMemoryProviderConfigStore()
        config = ProviderConfig(
            base_url="https://example.invalid/v1",
            model="test-model",
        )

        store.save(config)
        self.assertEqual(store.load(), config)

        store.clear()
        self.assertIsNone(store.load())


class MockLLMProviderTest(unittest.TestCase):
    def test_returns_deterministic_response_and_records_request(self) -> None:
        provider = MockLLMProvider(response_text="Fixed offline response")
        request = LLMRequest(
            prompt="Summarize the local fixture.",
            system_prompt="Use concise language.",
        )

        response = provider.complete(request)

        self.assertEqual(response.text, "Fixed offline response")
        self.assertEqual(provider.requests, (request,))

    def test_responder_can_derive_output_from_request(self) -> None:
        provider = MockLLMProvider(
            responder=lambda request: f"Received: {request.prompt}"
        )

        response = provider.complete(LLMRequest(prompt="Paragraph one"))

        self.assertEqual(response.text, "Received: Paragraph one")

    def test_failure_is_user_readable_and_does_not_expose_config(self) -> None:
        secret = "private-test-key"
        provider = MockLLMProvider(
            config=ProviderConfig(
                base_url="https://example.invalid/v1",
                model="test-model",
                api_key=secret,
            ),
            failure_message="Provider fixture is unavailable.",
        )

        with self.assertRaises(LLMProviderError) as context:
            provider.complete(LLMRequest(prompt="Local fixture"))

        self.assertEqual(
            str(context.exception),
            "Provider fixture is unavailable.",
        )
        self.assertNotIn(secret, str(context.exception))

    def test_connection_result_supports_success_and_failure(self) -> None:
        success = MockLLMProvider().test_connection()
        failure = MockLLMProvider(
            failure_message="Offline fixture failure."
        ).test_connection()

        self.assertTrue(success.success)
        self.assertFalse(failure.success)
        self.assertEqual(failure.message, "Offline fixture failure.")

    def test_empty_prompt_is_rejected_before_provider_call(self) -> None:
        with self.assertRaises(ValueError):
            LLMRequest(prompt="   ")


if __name__ == "__main__":
    unittest.main()
