import os
import sys
import threading
import time
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from mercury.agents import (
    InMemorySummaryResultStore,
    SummaryAgent,
    SummarySource,
)
from mercury.domain import SummaryDetail
from mercury.i18n import Translator
from mercury.llm import MockLLMProvider, ProviderConfig
from mercury.services.mock_article_service import MockArticleService
from mercury.ui.main_window import MainWindow
from mercury.ui.summary_panel import SummaryPanel


def configured_provider(
    response_text: str = "Fixed panel summary",
    failure_message: str | None = None,
) -> MockLLMProvider:
    return MockLLMProvider(
        response_text=response_text,
        failure_message=failure_message,
        config=ProviderConfig(
            base_url="http://127.0.0.1:8080/v1",
            model="panel-test-model",
            api_key="panel-test-secret",
        ),
    )


def summary_source(article_id: str = "article-1") -> SummarySource:
    return SummarySource(
        article_id=article_id,
        title=f"Title for {article_id}",
        raw_html="<p>Readable article body.</p>",
        cleaned_markdown="Readable **cleaned Markdown** body.",
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


class SummaryPanelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.panels: list[SummaryPanel] = []

    def tearDown(self) -> None:
        for panel in self.panels:
            panel._thread_pool.waitForDone(2000)
            panel.close()
            panel.deleteLater()

    def _panel(self, *args, **kwargs) -> SummaryPanel:
        panel = SummaryPanel(*args, **kwargs)
        self.panels.append(panel)
        return panel

    def _wait_for(self, spy: QSignalSpy) -> None:
        self.assertTrue(wait_for_signal(self.app, spy))

    def test_requires_an_article_and_generator_before_generation(self) -> None:
        panel = self._panel(Translator("en_US"))

        self.assertFalse(panel.generate_button.isEnabled())
        self.assertIn("Select an article", panel.status_label.text())

        panel.set_article(summary_source())

        self.assertTrue(panel.generate_button.isEnabled())
        self.assertIn("unavailable", panel.status_label.text())
        self.assertEqual(
            panel.generate_button.toolTip(),
            "Open AI settings.",
        )

        settings_spy = QSignalSpy(panel.settings_requested)
        panel.generate_button.click()
        self.assertEqual(settings_spy.count(), 1)

    def test_dark_color_scheme_uses_light_text_and_placeholder_roles(
        self,
    ) -> None:
        panel = self._panel(Translator("zh_CN"))

        panel.set_color_scheme("dark")

        prompt_palette = panel.prompt_edit.palette()
        combo_palette = panel.language_combo.palette()
        self.assertEqual(
            prompt_palette.color(QPalette.ColorRole.Text).name(),
            "#f3f6f9",
        )
        self.assertEqual(
            prompt_palette.color(QPalette.ColorRole.PlaceholderText).name(),
            "#b6c3cf",
        )
        self.assertEqual(
            combo_palette.color(QPalette.ColorRole.ButtonText).name(),
            "#f3f6f9",
        )

    def test_ai_settings_button_emits_request(self) -> None:
        panel = self._panel(Translator("zh_CN"))
        spy = QSignalSpy(panel.settings_requested)

        QTest.mouseClick(
            panel.configure_button,
            Qt.MouseButton.LeftButton,
        )

        self.assertEqual(spy.count(), 1)

    def test_generates_summary_asynchronously_and_shows_timestamp(self) -> None:
        provider = configured_provider()
        agent = SummaryAgent(provider)
        panel = self._panel(
            Translator("en_US"),
            generator=agent.summarize,
        )
        panel.set_article(summary_source())
        spy = QSignalSpy(panel.generation_completed)

        panel.generate_button.click()
        self._wait_for(spy)

        self.assertFalse(panel.is_running)
        self.assertEqual(
            panel.summary_content.toPlainText(),
            "Fixed panel summary",
        )
        self.assertEqual(panel.generate_button.text(), "Regenerate")
        self.assertIn("Generated:", panel.timestamp_label.text())

    def test_generation_does_not_block_the_ui_thread(self) -> None:
        started = threading.Event()
        release = threading.Event()
        agent = SummaryAgent(configured_provider())

        def delayed_generator(source, options):
            started.set()
            release.wait(2)
            return agent.summarize(source, options)

        panel = self._panel(
            Translator("en_US"),
            generator=delayed_generator,
        )
        panel.set_article(summary_source())
        spy = QSignalSpy(panel.generation_completed)

        panel.generate_button.click()

        self.assertTrue(started.wait(1))
        self.assertTrue(panel.is_running)
        self.assertFalse(panel.generate_button.isEnabled())
        self.assertIn("background", panel.status_label.text())

        release.set()
        self._wait_for(spy)

    def test_options_from_controls_enter_agent_request(self) -> None:
        provider = configured_provider()
        panel = self._panel(
            Translator("en_US"),
            generator=SummaryAgent(provider).summarize,
        )
        panel.set_article(summary_source())
        panel.language_combo.setCurrentIndex(
            panel.language_combo.findData("Simplified Chinese")
        )
        panel.detail_combo.setCurrentIndex(
            panel.detail_combo.findData(SummaryDetail.DETAILED.value)
        )
        panel.prompt_edit.setPlainText("Use evidence-first bullets.")
        spy = QSignalSpy(panel.generation_completed)

        panel.generate_button.click()
        self._wait_for(spy)

        request = provider.requests[0]
        self.assertIn("Summary language: Simplified Chinese", request.prompt)
        self.assertIn("Detail level: detailed", request.prompt)
        self.assertEqual(
            request.system_prompt,
            "Use evidence-first bullets.",
        )

    def test_regeneration_failure_keeps_previous_summary_visible(self) -> None:
        success_agent = SummaryAgent(
            configured_provider(response_text="Previous summary")
        )
        failure_agent = SummaryAgent(
            configured_provider(failure_message="offline fixture")
        )
        calls = 0

        def generator(source, options):
            nonlocal calls
            calls += 1
            agent = success_agent if calls == 1 else failure_agent
            return agent.summarize(source, options)

        panel = self._panel(
            Translator("en_US"),
            generator=generator,
        )
        panel.set_article(summary_source())

        first_spy = QSignalSpy(panel.generation_completed)
        panel.generate_button.click()
        self._wait_for(first_spy)
        second_spy = QSignalSpy(panel.generation_completed)
        panel.generate_button.click()
        self._wait_for(second_spy)

        self.assertEqual(
            panel.summary_content.toPlainText(),
            "Previous summary",
        )
        self.assertIn("article remains readable", panel.status_label.text())

    def test_switching_article_ignores_stale_background_result(self) -> None:
        started = threading.Event()
        release = threading.Event()
        agent = SummaryAgent(
            configured_provider(response_text="Stale first summary")
        )

        def delayed_generator(source, options):
            started.set()
            release.wait(2)
            return agent.summarize(source, options)

        panel = self._panel(
            Translator("en_US"),
            generator=delayed_generator,
        )
        panel.set_article(summary_source("article-1"))
        panel.generate_button.click()
        self.assertTrue(started.wait(1))

        panel.set_article(summary_source("article-2"))
        release.set()
        panel._thread_pool.waitForDone(2000)
        self.app.processEvents()

        self.assertEqual(panel.current_article_id, "article-2")
        self.assertNotIn(
            "Stale first summary",
            panel.summary_content.toPlainText(),
        )

    def test_existing_local_summary_is_loaded_for_article(self) -> None:
        store = InMemorySummaryResultStore()
        source = summary_source()
        result = SummaryAgent(
            configured_provider(response_text="Stored summary"),
            store,
        ).summarize(source)
        panel = self._panel(
            Translator("en_US"),
            generator=SummaryAgent(configured_provider()).summarize,
            result_loader=store.latest_for_article,
        )

        panel.set_article(source)

        self.assertEqual(panel.summary_content.toPlainText(), result.text)
        self.assertEqual(panel.generate_button.text(), "Regenerate")

    def test_runtime_language_switch_preserves_generated_summary(self) -> None:
        translator = Translator("en_US")
        panel = self._panel(
            translator,
            generator=SummaryAgent(configured_provider()).summarize,
        )
        panel.set_article(summary_source())
        spy = QSignalSpy(panel.generation_completed)
        panel.generate_button.click()
        self._wait_for(spy)

        translator.set_language("zh_CN")
        panel.set_translator(translator)

        self.assertEqual(
            panel.summary_content.toPlainText(),
            "Fixed panel summary",
        )
        self.assertEqual(panel.generate_button.text(), "重新生成")
        self.assertEqual(
            panel.detail_combo.currentData(),
            SummaryDetail.STANDARD.value,
        )


class MainWindowSummaryIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_mock_summary_appears_without_replacing_article(self) -> None:
        agent = SummaryAgent(
            configured_provider(response_text="Integrated summary")
        )
        window = MainWindow(
            MockArticleService(),
            summary_generator=agent.summarize,
        )
        window._show_article("mercury-start")
        reader_text = window.article_reader.content.toPlainText()
        spy = QSignalSpy(window.summary_panel.generation_completed)

        window.summary_panel.generate_button.click()
        self.assertTrue(wait_for_signal(self.app, spy))

        self.assertEqual(
            window.article_reader.current_article_id,
            "mercury-start",
        )
        self.assertEqual(
            window.article_reader.content.toPlainText(),
            reader_text,
        )
        self.assertEqual(
            window.summary_panel.summary_content.toPlainText(),
            "Integrated summary",
        )
        window.summary_panel._thread_pool.waitForDone(2000)
        window.close()
        window.deleteLater()

    def test_provider_failure_keeps_article_readable(self) -> None:
        agent = SummaryAgent(
            configured_provider(failure_message="offline fixture")
        )
        window = MainWindow(
            MockArticleService(),
            summary_generator=agent.summarize,
        )
        window._show_article("mercury-start")
        reader_text = window.article_reader.content.toPlainText()
        spy = QSignalSpy(window.summary_panel.generation_completed)

        window.summary_panel.generate_button.click()
        self.assertTrue(wait_for_signal(self.app, spy))

        self.assertEqual(
            window.article_reader.content.toPlainText(),
            reader_text,
        )
        self.assertIn(
            "仍可正常阅读",
            window.summary_panel.status_label.text(),
        )
        window.summary_panel._thread_pool.waitForDone(2000)
        window.close()
        window.deleteLater()

    def test_closed_summary_dock_can_be_reopened_from_view_action(self) -> None:
        window = MainWindow(MockArticleService())
        window.show()
        self.app.processEvents()

        window.summary_dock.close()
        self.app.processEvents()

        self.assertFalse(window.summary_dock.isVisible())
        self.assertFalse(window.toggle_summary_action.isChecked())

        window.toggle_summary_action.trigger()
        self.app.processEvents()

        self.assertTrue(window.summary_dock.isVisible())
        self.assertTrue(window.toggle_summary_action.isChecked())
        window.close()
        window.deleteLater()


if __name__ == "__main__":
    unittest.main()
