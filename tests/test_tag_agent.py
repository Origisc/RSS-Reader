import os
import sys
import time
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

for path in (PROJECT_ROOT, SRC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from mercury.agents import (
    TagAgent,
    TagSource,
    TagSuggestionErrorCode,
    TagSuggestionOptions,
    parse_tag_suggestions,
)
from mercury.i18n import Translator
from mercury.llm import MockLLMProvider, ProviderConfig
from mercury.services.mock_article_service import MockArticleService
from mercury.ui.main_window import MainWindow
from mercury.ui.tag_suggestion_panel import TagSuggestionPanel


def configured_provider(
    response_text: str = '["Python", "Local first"]',
    *,
    failure_message: str | None = None,
) -> MockLLMProvider:
    return MockLLMProvider(
        response_text=response_text,
        failure_message=failure_message,
        config=ProviderConfig(
            base_url="http://127.0.0.1:8080/v1",
            model="tag-test-model",
            api_key="tag-test-secret",
        ),
    )


def tag_source(article_id: str = "article-1") -> TagSource:
    return TagSource(
        article_id=article_id,
        title="A local-first Python reader",
        raw_html="<p>Fallback article body.</p>",
        cleaned_markdown="A **Python** RSS reader that stores data locally.",
        existing_tags=("Python", "Privacy"),
        assigned_tags=("Already assigned",),
    )


def wait_for_signal(
    app: QApplication,
    spy: QSignalSpy,
    timeout_seconds: float = 2.0,
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while spy.count() == 0 and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    return spy.count() > 0


class TagAgentTest(unittest.TestCase):
    def test_generates_deduplicated_suggestions_with_unified_provider(
        self,
    ) -> None:
        provider = configured_provider(
            '["Python", "python", "Local first", "Already assigned"]'
        )
        result = TagAgent(provider).suggest(tag_source())

        self.assertEqual(result.suggestions, ("Python", "Local first"))
        self.assertEqual(result.provider_model, "tag-test-model")
        self.assertIn("Existing local tags", provider.requests[0].prompt)
        self.assertIn(
            "return only a JSON array",
            provider.requests[0].system_prompt,
        )

    def test_custom_prompt_enters_request_without_replacing_json_contract(
        self,
    ) -> None:
        provider = configured_provider('["人工智能"]')
        result = TagAgent(provider).suggest(
            tag_source(),
            TagSuggestionOptions(
                custom_prompt="Use Simplified Chinese tags.",
                max_suggestions=3,
            ),
        )

        self.assertEqual(result.suggestions, ("人工智能",))
        request = provider.requests[0]
        self.assertIn("Use Simplified Chinese tags.", request.system_prompt)
        self.assertIn("Maximum suggestions: 3", request.prompt)
        self.assertIn("return only a JSON array", request.system_prompt)

    def test_unconfigured_or_failed_provider_returns_safe_result(self) -> None:
        unconfigured = TagAgent(MockLLMProvider()).suggest(tag_source())
        self.assertEqual(
            unconfigured.error_code,
            TagSuggestionErrorCode.PROVIDER_NOT_CONFIGURED,
        )

        failed = TagAgent(
            configured_provider(
                failure_message="Rejected tag-test-secret",
            )
        ).suggest(tag_source())
        self.assertEqual(
            failed.error_code,
            TagSuggestionErrorCode.PROVIDER_FAILURE,
        )
        self.assertNotIn("tag-test-secret", failed.error_message or "")

    def test_plain_text_fallback_is_bounded_and_normalized(self) -> None:
        parsed = parse_tag_suggestions(
            "- Python\n2. Local first\n#Privacy\nPython",
            max_suggestions=3,
        )

        self.assertEqual(parsed, ("Python", "Local first", "Privacy"))


class TagSuggestionPanelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.panels: list[TagSuggestionPanel] = []

    def tearDown(self) -> None:
        for panel in self.panels:
            panel._thread_pool.waitForDone(2000)
            panel.close()
            panel.deleteLater()

    def _panel(self, *args, **kwargs) -> TagSuggestionPanel:
        panel = TagSuggestionPanel(*args, **kwargs)
        self.panels.append(panel)
        return panel

    def test_suggestions_require_explicit_apply(self) -> None:
        panel = self._panel(
            Translator("en_US"),
            generator=TagAgent(configured_provider()).suggest,
        )
        panel.set_article(tag_source())
        generated = QSignalSpy(panel.generation_completed)
        applied = QSignalSpy(panel.apply_requested)

        panel.generate_button.click()
        self.assertTrue(wait_for_signal(self.app, generated))

        self.assertEqual(panel.suggestion_list.count(), 2)
        self.assertEqual(applied.count(), 0)
        panel.apply_button.click()
        self.assertEqual(applied.count(), 1)
        self.assertEqual(applied.at(0)[0], "article-1")
        self.assertEqual(applied.at(0)[1], ("Python", "Local first"))

    def test_dismiss_and_article_switch_never_apply_suggestions(self) -> None:
        panel = self._panel(
            Translator("en_US"),
            generator=TagAgent(configured_provider()).suggest,
        )
        panel.set_article(tag_source())
        generated = QSignalSpy(panel.generation_completed)
        applied = QSignalSpy(panel.apply_requested)
        panel.generate_button.click()
        self.assertTrue(wait_for_signal(self.app, generated))

        panel.dismiss_button.click()
        panel.set_article(tag_source("article-2"))

        self.assertEqual(panel.suggestion_list.count(), 0)
        self.assertEqual(applied.count(), 0)

    def test_unavailable_agent_opens_ai_settings(self) -> None:
        panel = self._panel(Translator("en_US"))
        panel.set_article(tag_source())
        settings = QSignalSpy(panel.settings_requested)

        panel.generate_button.click()

        self.assertEqual(settings.count(), 1)


class MainWindowTagAgentIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_confirmed_suggestions_use_manual_tag_service(self) -> None:
        service = MockArticleService()
        agent = TagAgent(
            configured_provider('["Python", "本地优先", "AI, ML"]')
        )
        window = MainWindow(
            service,
            tag_suggestion_generator=agent.suggest,
        )
        window._show_article("mercury-start")
        generated = QSignalSpy(
            window.tag_suggestion_panel.generation_completed
        )

        window.tag_suggestion_panel.generate_button.click()
        self.assertTrue(wait_for_signal(self.app, generated))
        self.assertEqual(
            service.list_article_tags("mercury-start"),
            [],
        )

        window.tag_suggestion_panel.apply_button.click()
        self.assertEqual(
            {
                tag.name
                for tag in service.list_article_tags("mercury-start")
            },
            {"Python", "本地优先", "AI, ML"},
        )
        window.tag_suggestion_panel._thread_pool.waitForDone(2000)
        window.close()
        window.deleteLater()


if __name__ == "__main__":
    unittest.main()
