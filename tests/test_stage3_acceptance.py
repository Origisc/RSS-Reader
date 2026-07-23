import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "llm" / (
    "stage3_article.json"
)

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.agents import (
    SummaryAgent,
    SummarySource,
    TranslationAgent,
    TranslationSource,
)
from mercury.domain import (
    SummaryErrorCode,
    TranslationErrorCode,
    TranslationStatus,
)
from mercury.llm import MockLLMProvider, ProviderConfig


def configured_provider(**kwargs) -> MockLLMProvider:
    return MockLLMProvider(
        config=ProviderConfig(
            base_url="http://127.0.0.1:8080/v1",
            model="stage-3-mock-model",
            api_key="offline-test-secret",
        ),
        **kwargs,
    )


class Stage3AcceptanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.markdown = "\n\n".join(
            item["original"]
            for item in cls.fixture["paragraphs"]
        )
        cls.summary_source = SummarySource(
            article_id=cls.fixture["article_id"],
            title=cls.fixture["title"],
            raw_html="",
            cleaned_markdown=cls.markdown,
        )
        cls.translation_source = TranslationSource(
            article_id=cls.fixture["article_id"],
            title=cls.fixture["title"],
            raw_html="",
            cleaned_markdown=cls.markdown,
        )

    def test_mock_provider_verifies_summary_and_aligned_translation(
        self,
    ) -> None:
        summary_provider = configured_provider(
            response_text=self.fixture["summary"]
        )

        def translate_response(request) -> str:
            for item in self.fixture["paragraphs"]:
                if item["original"] in request.prompt:
                    return item["translated"]
            return ""

        translation_provider = configured_provider(
            responder=translate_response
        )

        summary = SummaryAgent(summary_provider).summarize(
            self.summary_source
        )
        translation = TranslationAgent(
            translation_provider
        ).translate(self.translation_source)

        self.assertTrue(summary.succeeded)
        self.assertEqual(summary.text, self.fixture["summary"])
        self.assertIs(translation.status, TranslationStatus.COMPLETED)
        self.assertEqual(
            translation.original_paragraphs,
            tuple(
                item["original"]
                for item in self.fixture["paragraphs"]
            ),
        )
        self.assertEqual(
            tuple(
                item.translated_text
                for item in translation.paragraphs
            ),
            tuple(
                item["translated"]
                for item in self.fixture["paragraphs"]
            ),
        )
        self.assertEqual(
            len(translation_provider.requests),
            len(self.fixture["paragraphs"]),
        )

    def test_mock_failure_keeps_translation_originals_readable(
        self,
    ) -> None:
        provider = configured_provider(
            failure_message="Deliberate offline acceptance failure."
        )

        summary = SummaryAgent(provider).summarize(self.summary_source)
        translation = TranslationAgent(provider).translate(
            self.translation_source
        )

        self.assertFalse(summary.has_summary)
        self.assertIs(
            summary.error_code,
            SummaryErrorCode.PROVIDER_FAILURE,
        )
        self.assertIs(translation.status, TranslationStatus.FAILED)
        self.assertIs(
            translation.error_code,
            TranslationErrorCode.PROVIDER_FAILURE,
        )
        self.assertEqual(
            translation.original_paragraphs,
            tuple(
                item["original"]
                for item in self.fixture["paragraphs"]
            ),
        )
        self.assertTrue(
            all(
                not paragraph.translated_text
                for paragraph in translation.paragraphs
            )
        )


if __name__ == "__main__":
    unittest.main()
