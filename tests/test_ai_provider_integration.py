import os
import sys
import time
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from mercury.agents import (
    InMemorySummaryResultStore,
    InMemoryTranslationResultStore,
    SummaryAgent,
    TranslationAgent,
)
from mercury.llm import (
    HTTPChatCompletionsProvider,
    InMemoryProviderConfigStore,
    ProviderConfig,
)
from mercury.services.mock_article_service import MockArticleService
from mercury.ui.main_window import MainWindow


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


class AIProviderIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_saved_settings_power_summary_and_translation_agents(
        self,
    ) -> None:
        calls: list[dict[str, object]] = []

        def transport(_url, headers, payload, _timeout):
            calls.append(
                {
                    "headers": dict(headers),
                    "payload": dict(payload),
                }
            )
            messages = payload["messages"]
            user_prompt = messages[-1]["content"]
            response_text = (
                "逐段译文"
                if "Target language:" in user_prompt
                else "Summary through the HTTP adapter"
            )
            return {
                "choices": [
                    {
                        "message": {
                            "content": response_text,
                        }
                    }
                ]
            }

        config_store = InMemoryProviderConfigStore()
        provider = HTTPChatCompletionsProvider(
            config_store,
            transport,
        )
        summary_store = InMemorySummaryResultStore()
        translation_store = InMemoryTranslationResultStore()
        summary_agent = SummaryAgent(provider, summary_store)
        translation_agent = TranslationAgent(
            provider,
            translation_store,
        )
        window = MainWindow(
            MockArticleService(),
            provider_config_store=config_store,
            provider_connection_tester=provider.test_config,
            summary_generator=summary_agent.summarize,
            summary_result_loader=summary_store.latest_for_article,
            translation_generator=translation_agent.translate,
            translation_result_loader=(
                translation_store.latest_for_article
            ),
        )
        window.show()
        window._show_article("mercury-start")

        config_store.save(
            ProviderConfig(
                base_url="http://127.0.0.1:8080/v1",
                model="integration-model",
                api_key="integration-secret",
            )
        )

        summary_spy = QSignalSpy(
            window.summary_panel.generation_completed
        )
        window.summary_panel.generate_button.click()
        self.assertTrue(wait_for_signal(self.app, summary_spy))
        self.assertEqual(
            window.summary_panel.summary_content.toPlainText(),
            "Summary through the HTTP adapter",
        )

        translation_spy = QSignalSpy(
            window.translation_panel.generation_completed
        )
        window.translation_panel.generate_button.click()
        self.assertTrue(wait_for_signal(self.app, translation_spy))
        rendered_translation = (
            window.article_reader.content.toPlainText()
        )
        displayed_result = window.translation_panel.displayed_result
        self.assertIsNotNone(displayed_result)
        self.assertTrue(window.article_reader.bilingual_visible)
        self.assertTrue(
            all(
                paragraph.translated_text == "逐段译文"
                for paragraph in displayed_result.paragraphs
            )
        )
        cursor = 0
        for paragraph in displayed_result.paragraphs:
            original_position = rendered_translation.index(
                paragraph.original_text,
                cursor,
            )
            translation_position = rendered_translation.index(
                paragraph.translated_text,
                original_position + len(paragraph.original_text),
            )
            self.assertLess(original_position, translation_position)
            cursor = translation_position + len(paragraph.translated_text)
        self.assertFalse(window.translation_panel.isVisible())
        self.assertEqual(
            len(calls),
            1 + len(displayed_result.paragraphs),
        )
        self.assertTrue(
            all(
                call["payload"]["model"] == "integration-model"
                for call in calls
            )
        )
        self.assertTrue(
            all(
                call["headers"]["Authorization"]
                == "Bearer integration-secret"
                for call in calls
            )
        )

        window.summary_panel._thread_pool.waitForDone(2000)
        window.translation_panel._thread_pool.waitForDone(2000)
        window.close()
        window.deleteLater()


if __name__ == "__main__":
    unittest.main()
