import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.agents import (
    InMemoryTranslationResultStore,
    TranslationAgent,
    TranslationOptions,
    TranslationSource,
    extract_translation_paragraphs,
    segment_translation_text,
)
from mercury.domain import (
    TranslationErrorCode,
    TranslationParagraphStatus,
    TranslationSourceFormat,
    TranslationStatus,
)
from mercury.llm import (
    LLMProviderError,
    MockLLMProvider,
    ProviderConfig,
)


TEST_TIME = datetime(2026, 7, 19, 9, 0, tzinfo=UTC)


def configured_provider(**kwargs) -> MockLLMProvider:
    return MockLLMProvider(
        config=ProviderConfig(
            base_url="http://127.0.0.1:8080/v1",
            model="user-selected-translation-model",
            api_key="translation-test-secret",
        ),
        **kwargs,
    )


def requested_text(request) -> str:
    return request.prompt.split("Text to translate:\n", 1)[1]


class TranslationTextProcessingTest(unittest.TestCase):
    def test_extracts_markdown_paragraphs_in_order(self) -> None:
        paragraphs = extract_translation_paragraphs(
            TranslationSourceFormat.CLEANED_MARKDOWN,
            "First paragraph.\n\nSecond paragraph.\ncontinued\n\nThird.",
        )

        self.assertEqual(
            paragraphs,
            (
                "First paragraph.",
                "Second paragraph.\ncontinued",
                "Third.",
            ),
        )

    def test_extracts_html_blocks_and_ignores_script_content(self) -> None:
        paragraphs = extract_translation_paragraphs(
            TranslationSourceFormat.CLEANED_HTML,
            (
                "<p>First <strong>bold</strong>.</p>"
                "<script>private script text</script>"
                "<ul><li>Second item</li><li>Third item</li></ul>"
            ),
        )

        self.assertEqual(
            paragraphs,
            ("First bold.", "Second item", "Third item"),
        )

    def test_long_text_segments_preserve_order(self) -> None:
        text = "one two three four five six seven eight nine ten eleven"

        segments = segment_translation_text(text, max_chars=20)

        self.assertGreater(len(segments), 1)
        self.assertTrue(all(len(segment) <= 20 for segment in segments))
        self.assertEqual(" ".join(segments), text)


class TranslationAgentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = TranslationSource(
            article_id="article-1",
            title="Local-first article",
            raw_html="<p>Raw first.</p><p>Raw second.</p>",
            cleaned_html="<p>HTML first.</p><p>HTML second.</p>",
            cleaned_markdown="Markdown first.\n\nMarkdown second.",
        )

    def test_mock_provider_translates_paragraphs_in_order_and_saves(
        self,
    ) -> None:
        store = InMemoryTranslationResultStore()
        provider = configured_provider(
            responder=lambda request: f"译：{requested_text(request)}"
        )
        agent = TranslationAgent(provider, store, clock=lambda: TEST_TIME)

        result = agent.translate(self.source)

        self.assertEqual(result.status, TranslationStatus.COMPLETED)
        self.assertTrue(result.is_saved)
        self.assertEqual(result.generated_at, TEST_TIME)
        self.assertEqual(
            result.original_paragraphs,
            ("Markdown first.", "Markdown second."),
        )
        self.assertEqual(
            tuple(paragraph.index for paragraph in result.paragraphs),
            (0, 1),
        )
        self.assertEqual(
            tuple(paragraph.translated_text for paragraph in result.paragraphs),
            ("译：Markdown first.", "译：Markdown second."),
        )
        self.assertEqual(store.latest_for_article("article-1"), result)

    def test_cleaned_markdown_has_priority_over_html_and_raw(self) -> None:
        provider = configured_provider(response_text="translated")

        result = TranslationAgent(provider).translate(self.source)

        self.assertEqual(
            result.source_format,
            TranslationSourceFormat.CLEANED_MARKDOWN,
        )
        prompts = "\n".join(request.prompt for request in provider.requests)
        self.assertIn("Markdown first", prompts)
        self.assertNotIn("HTML first", prompts)
        self.assertNotIn("Raw first", prompts)

    def test_target_language_and_custom_prompt_enter_request(self) -> None:
        provider = configured_provider(response_text="translation")
        options = TranslationOptions(
            target_language="Japanese",
            custom_prompt="Translate technical terms consistently.",
        )

        TranslationAgent(provider).translate(self.source, options)

        request = provider.requests[0]
        self.assertIn("Target language: Japanese", request.prompt)
        self.assertEqual(
            request.system_prompt,
            "Translate technical terms consistently.",
        )

    def test_long_paragraph_is_translated_in_multiple_segments(self) -> None:
        long_text = (
            "Alpha beta gamma delta epsilon zeta eta theta iota kappa "
            "lambda mu nu xi omicron."
        )
        source = TranslationSource(
            article_id="long",
            title="Long article",
            raw_html="",
            cleaned_markdown=long_text,
        )
        provider = configured_provider(
            responder=lambda request: f"T:{requested_text(request)}"
        )

        result = TranslationAgent(provider).translate(
            source,
            TranslationOptions(max_segment_chars=24),
        )

        paragraph = result.paragraphs[0]
        self.assertGreater(paragraph.segment_count, 1)
        self.assertEqual(
            paragraph.segment_count,
            paragraph.translated_segment_count,
        )
        self.assertEqual(len(provider.requests), paragraph.segment_count)
        self.assertEqual(
            paragraph.status,
            TranslationParagraphStatus.TRANSLATED,
        )
        self.assertEqual(paragraph.original_text, long_text)

    def test_one_paragraph_failure_keeps_original_and_continues(self) -> None:
        calls = 0

        def responder(request):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise LLMProviderError("second paragraph fixture failure")
            return f"T:{requested_text(request)}"

        provider = configured_provider(responder=responder)
        source = TranslationSource(
            article_id="partial",
            title="Partial translation",
            raw_html="",
            cleaned_markdown="First.\n\nSecond.\n\nThird.",
        )

        result = TranslationAgent(provider).translate(source)

        self.assertEqual(result.status, TranslationStatus.PARTIAL)
        self.assertEqual(
            result.original_paragraphs,
            ("First.", "Second.", "Third."),
        )
        self.assertEqual(
            result.paragraphs[1].status,
            TranslationParagraphStatus.FAILED,
        )
        self.assertEqual(result.paragraphs[1].original_text, "Second.")
        self.assertFalse(result.paragraphs[1].has_translation)
        self.assertEqual(result.paragraphs[2].translated_text, "T:Third.")
        self.assertEqual(len(provider.requests), 3)

    def test_one_long_paragraph_segment_failure_keeps_full_original(self) -> None:
        calls = 0

        def responder(request):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise LLMProviderError("middle segment fixture failure")
            return f"T:{requested_text(request)}"

        original = (
            "Alpha beta gamma delta epsilon zeta eta theta iota kappa "
            "lambda mu nu xi omicron."
        )
        provider = configured_provider(responder=responder)
        result = TranslationAgent(provider).translate(
            TranslationSource(
                article_id="partial-segment",
                title="Partial segment",
                raw_html="",
                cleaned_markdown=original,
            ),
            TranslationOptions(max_segment_chars=24),
        )

        paragraph = result.paragraphs[0]
        self.assertEqual(result.status, TranslationStatus.PARTIAL)
        self.assertEqual(
            paragraph.status,
            TranslationParagraphStatus.PARTIAL,
        )
        self.assertEqual(paragraph.original_text, original)
        self.assertEqual(
            paragraph.translated_segment_count,
            paragraph.segment_count - 1,
        )
        self.assertEqual(len(provider.requests), paragraph.segment_count)

    def test_empty_segment_response_does_not_drop_later_paragraphs(self) -> None:
        calls = 0

        def responder(request):
            nonlocal calls
            calls += 1
            return "" if calls == 2 else f"T:{requested_text(request)}"

        result = TranslationAgent(
            configured_provider(responder=responder)
        ).translate(
            TranslationSource(
                article_id="empty-segment",
                title="Empty segment",
                raw_html="",
                cleaned_markdown="One.\n\nTwo.\n\nThree.",
            )
        )

        self.assertEqual(
            result.paragraphs[1].error_code,
            TranslationErrorCode.EMPTY_RESPONSE,
        )
        self.assertEqual(result.paragraphs[2].translated_text, "T:Three.")

    def test_unconfigured_provider_returns_all_originals_without_call(self) -> None:
        provider = MockLLMProvider(response_text="must not be used")

        result = TranslationAgent(provider).translate(self.source)

        self.assertEqual(result.status, TranslationStatus.FAILED)
        self.assertEqual(
            result.error_code,
            TranslationErrorCode.PROVIDER_NOT_CONFIGURED,
        )
        self.assertEqual(
            result.original_paragraphs,
            ("Markdown first.", "Markdown second."),
        )
        self.assertTrue(
            all(
                paragraph.status is TranslationParagraphStatus.FAILED
                for paragraph in result.paragraphs
            )
        )
        self.assertEqual(provider.requests, ())

    def test_provider_error_redacts_api_key(self) -> None:
        secret = "translation-test-secret"
        provider = configured_provider(
            failure_message=f"Credential {secret} rejected"
        )

        result = TranslationAgent(provider).translate(self.source)

        self.assertNotIn(secret, result.paragraphs[0].error_message)
        self.assertIn("••••", result.paragraphs[0].error_message)
        self.assertEqual(
            result.original_paragraphs,
            ("Markdown first.", "Markdown second."),
        )

    def test_storage_failure_keeps_translation_available(self) -> None:
        class FailingStore:
            def save(self, result) -> None:
                raise OSError("local fixture unavailable")

            def latest_for_article(self, article_id: str):
                return None

        result = TranslationAgent(
            configured_provider(response_text="Still readable"),
            FailingStore(),
        ).translate(self.source)

        self.assertTrue(result.has_translations)
        self.assertFalse(result.is_saved)
        self.assertEqual(
            result.storage_error_code,
            TranslationErrorCode.STORAGE_FAILURE,
        )
        self.assertIn("could not be saved", result.storage_error_message)

    def test_missing_content_returns_failure_without_provider_call(self) -> None:
        provider = configured_provider(response_text="must not be used")
        source = TranslationSource(
            article_id="empty",
            title="Empty",
            raw_html="  ",
        )

        result = TranslationAgent(provider).translate(source)

        self.assertEqual(result.status, TranslationStatus.FAILED)
        self.assertEqual(result.error_code, TranslationErrorCode.INVALID_INPUT)
        self.assertEqual(result.paragraphs, ())
        self.assertEqual(provider.requests, ())


if __name__ == "__main__":
    unittest.main()
