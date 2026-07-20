import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.agents import (
    InMemorySummaryResultStore,
    SummaryAgent,
    SummaryOptions,
    SummarySource,
)
from mercury.domain import (
    SummaryDetail,
    SummaryErrorCode,
    SummarySourceFormat,
    SummaryStatus,
)
from mercury.llm import MockLLMProvider, ProviderConfig


TEST_TIME = datetime(2026, 7, 18, 8, 30, tzinfo=UTC)


def configured_provider(**kwargs) -> MockLLMProvider:
    return MockLLMProvider(
        config=ProviderConfig(
            base_url="http://127.0.0.1:8080/v1",
            model="user-selected-model",
            api_key="test-secret",
        ),
        **kwargs,
    )


class SummaryAgentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = SummarySource(
            article_id="article-1",
            title="Local-first reading",
            raw_html="<p>Raw article content.</p>",
            cleaned_html="<p>Clean HTML content.</p>",
            cleaned_markdown="Clean **Markdown** content.",
        )

    def test_mock_provider_generates_and_saves_deterministic_summary(
        self,
    ) -> None:
        store = InMemorySummaryResultStore()
        provider = configured_provider(response_text="Fixed local summary")
        agent = SummaryAgent(provider, store, clock=lambda: TEST_TIME)

        result = agent.summarize(self.source)

        self.assertTrue(result.succeeded)
        self.assertTrue(result.is_saved)
        self.assertEqual(result.text, "Fixed local summary")
        self.assertEqual(result.generated_at, TEST_TIME)
        self.assertEqual(store.latest_for_article("article-1"), result)

    def test_cleaned_markdown_has_priority_over_other_content(self) -> None:
        provider = configured_provider(response_text="Summary")
        result = SummaryAgent(provider).summarize(self.source)

        request = provider.requests[0]
        self.assertEqual(
            result.source_format,
            SummarySourceFormat.CLEANED_MARKDOWN,
        )
        self.assertIn("Clean **Markdown** content.", request.prompt)
        self.assertNotIn("Clean HTML content", request.prompt)
        self.assertNotIn("Raw article content", request.prompt)

    def test_cleaned_html_then_raw_html_are_used_as_fallbacks(self) -> None:
        provider = configured_provider(response_text="Summary")
        html_source = SummarySource(
            article_id="html",
            title="HTML",
            raw_html="<p>Raw fallback</p>",
            cleaned_html="<p>Cleaned HTML</p>",
        )
        raw_source = SummarySource(
            article_id="raw",
            title="Raw",
            raw_html="<p>Raw fallback</p>",
        )
        agent = SummaryAgent(provider)

        html_result = agent.summarize(html_source)
        raw_result = agent.summarize(raw_source)

        self.assertEqual(
            html_result.source_format,
            SummarySourceFormat.CLEANED_HTML,
        )
        self.assertEqual(
            raw_result.source_format,
            SummarySourceFormat.RAW_HTML,
        )

    def test_language_and_detail_level_enter_the_prompt(self) -> None:
        provider = configured_provider(response_text="摘要")
        options = SummaryOptions(
            language="简体中文",
            detail_level=SummaryDetail.DETAILED,
        )

        SummaryAgent(provider).summarize(self.source, options)

        request = provider.requests[0]
        self.assertIn("Summary language: 简体中文", request.prompt)
        self.assertIn("Detail level: detailed", request.prompt)
        self.assertIn("thorough structured summary", request.prompt)

    def test_custom_prompt_replaces_default_system_prompt(self) -> None:
        provider = configured_provider(response_text="Summary")
        options = SummaryOptions(
            custom_prompt="Use a neutral, evidence-first style."
        )

        SummaryAgent(provider).summarize(self.source, options)

        self.assertEqual(
            provider.requests[0].system_prompt,
            "Use a neutral, evidence-first style.",
        )

    def test_unconfigured_provider_returns_failure_without_calling_it(
        self,
    ) -> None:
        provider = MockLLMProvider(response_text="Must not be used")

        result = SummaryAgent(provider).summarize(self.source)

        self.assertEqual(result.status, SummaryStatus.FAILED)
        self.assertEqual(
            result.error_code,
            SummaryErrorCode.PROVIDER_NOT_CONFIGURED,
        )
        self.assertIn("not configured", result.error_message)
        self.assertEqual(provider.requests, ())

    def test_provider_failure_is_readable_and_api_key_is_redacted(self) -> None:
        secret = "test-secret"
        provider = configured_provider(
            failure_message=f"Credential {secret} was rejected."
        )

        result = SummaryAgent(provider).summarize(self.source)

        self.assertFalse(result.has_summary)
        self.assertEqual(result.error_code, SummaryErrorCode.PROVIDER_FAILURE)
        self.assertNotIn(secret, result.error_message)
        self.assertIn("••••", result.error_message)

    def test_empty_provider_response_returns_failure(self) -> None:
        result = SummaryAgent(
            configured_provider(response_text="   ")
        ).summarize(self.source)

        self.assertEqual(result.error_code, SummaryErrorCode.EMPTY_RESPONSE)
        self.assertIn("empty summary", result.error_message)

    def test_missing_content_returns_failure_without_provider_call(self) -> None:
        provider = configured_provider(response_text="Must not be used")
        source = SummarySource(
            article_id="empty",
            title="Empty article",
            raw_html="   ",
        )

        result = SummaryAgent(provider).summarize(source)

        self.assertEqual(result.error_code, SummaryErrorCode.INVALID_INPUT)
        self.assertIn("No readable article content", result.error_message)
        self.assertEqual(provider.requests, ())

    def test_storage_failure_keeps_generated_summary_available(self) -> None:
        class FailingStore:
            def save(self, result) -> None:
                raise OSError("local fixture unavailable")

            def latest_for_article(self, article_id: str):
                return None

        result = SummaryAgent(
            configured_provider(response_text="Still readable"),
            FailingStore(),
        ).summarize(self.source)

        self.assertTrue(result.has_summary)
        self.assertTrue(result.succeeded)
        self.assertFalse(result.is_saved)
        self.assertEqual(result.status, SummaryStatus.GENERATED_NOT_SAVED)
        self.assertEqual(result.error_code, SummaryErrorCode.STORAGE_FAILURE)


if __name__ == "__main__":
    unittest.main()
