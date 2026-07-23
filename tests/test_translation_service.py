import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.llm.provider import (
    LLMProviderError,
    LLMRequest,
    LLMResponse,
    MockLLMProvider,
)
from mercury.services.translation_service import TranslationService


class FailingOnCallProvider:
    """Deterministic provider used to exercise paragraph fallbacks."""

    def __init__(self, fail_on_call: int | None = None) -> None:
        self.fail_on_call = fail_on_call
        self.requests: list[LLMRequest] = []

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        if self.fail_on_call == len(self.requests):
            raise LLMProviderError("API error")
        return LLMResponse(text="Translated paragraph")


class TranslationServiceTest(unittest.TestCase):
    def test_rejects_empty_text_without_calling_provider(self) -> None:
        provider = MockLLMProvider()
        service = TranslationService(provider)

        result = service.translate("   ")

        self.assertFalse(result.success)
        self.assertIn("empty", (result.error_message or "").lower())
        self.assertEqual(provider.requests, ())

    def test_translates_single_paragraph(self) -> None:
        provider = MockLLMProvider(response_text="翻译后的文本")
        service = TranslationService(provider)

        result = service.translate("This is a test paragraph.")

        self.assertTrue(result.success)
        self.assertEqual(result.translated_text, "翻译后的文本")
        self.assertEqual(result.paragraph_count, 1)
        self.assertEqual(result.failed_paragraphs, 0)

    def test_translates_each_paragraph_independently(self) -> None:
        provider = MockLLMProvider(response_text="翻译段落")
        service = TranslationService(provider)
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."

        result = service.translate(text)

        self.assertTrue(result.success)
        self.assertEqual(result.paragraph_count, 3)
        self.assertEqual(result.failed_paragraphs, 0)
        self.assertEqual(len(provider.requests), 3)

    def test_partial_failure_keeps_failed_paragraph_original(self) -> None:
        provider = FailingOnCallProvider(fail_on_call=2)
        service = TranslationService(provider)
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."

        translated_text, pairs = service.translate_with_comparison(text)

        self.assertEqual(len(pairs), 3)
        self.assertTrue(pairs[0].success)
        self.assertFalse(pairs[1].success)
        self.assertEqual(pairs[1].translated, "Second paragraph.")
        self.assertIn("Second paragraph.", translated_text)

    def test_complete_failure_returns_original_text_as_fallback(self) -> None:
        provider = MockLLMProvider(failure_message="All failed")
        service = TranslationService(provider)
        text = "First paragraph.\n\nSecond paragraph."

        result = service.translate(text)

        self.assertFalse(result.success)
        self.assertEqual(result.failed_paragraphs, 2)
        self.assertEqual(result.translated_text, text)

    def test_split_into_paragraphs_joins_wrapped_lines(self) -> None:
        service = TranslationService(MockLLMProvider())
        text = "Line 1\nLine 2\n\nLine 3\n\nLine 4\nLine 5"

        paragraphs = service._split_into_paragraphs(text)

        self.assertEqual(
            paragraphs,
            ["Line 1 Line 2", "Line 3", "Line 4 Line 5"],
        )

    def test_comparison_compatibility_alias(self) -> None:
        service = TranslationService(
            MockLLMProvider(response_text="翻译段落")
        )

        translated_text, pairs = service.translate_with对照(
            "First paragraph.\n\nSecond paragraph."
        )

        self.assertTrue(translated_text)
        self.assertEqual(len(pairs), 2)

    def test_reports_provider_implementation_name(self) -> None:
        service = TranslationService(MockLLMProvider())

        self.assertEqual(service.get_provider_name(), "MockLLMProvider")

    def test_target_language_is_in_provider_request(self) -> None:
        provider = MockLLMProvider(response_text="Japanese translation")
        service = TranslationService(provider)

        result = service.translate("English text", target_language="ja")

        self.assertTrue(result.success)
        self.assertIn("ja", provider.requests[0].prompt)


if __name__ == "__main__":
    unittest.main()
