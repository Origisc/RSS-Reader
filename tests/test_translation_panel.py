import os
import sys
import time
import unittest
from datetime import UTC, datetime
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtGui import QPalette
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from mercury.agents import TranslationOptions, TranslationSource
from mercury.domain import (
    TranslationErrorCode,
    TranslationParagraph,
    TranslationParagraphStatus,
    TranslationResult,
    TranslationSourceFormat,
    TranslationStatus,
)
from mercury.i18n import Translator
from mercury.services.mock_article_service import MockArticleService
from mercury.ui.bilingual_state import InMemoryBilingualViewStateStore
from mercury.ui.main_window import MainWindow
from mercury.ui.translation_panel import TranslationPanel


def translation_source(
    article_id: str = "article-1",
) -> TranslationSource:
    return TranslationSource(
        article_id=article_id,
        title=f"Title for {article_id}",
        raw_html="<p>Raw paragraph.</p>",
        cleaned_markdown="First original.\n\nSecond original.",
    )


def paragraph(
    index: int,
    original: str,
    translated: str,
    status: TranslationParagraphStatus,
    error_code: TranslationErrorCode | None = None,
) -> TranslationParagraph:
    return TranslationParagraph(
        index=index,
        original_text=original,
        translated_text=translated,
        status=status,
        segment_count=1,
        translated_segment_count=1 if translated else 0,
        error_code=error_code,
        error_message="Backend details are not rendered by the UI.",
    )


def translation_result(
    *,
    article_id: str = "article-1",
    paragraphs: tuple[TranslationParagraph, ...],
    status: TranslationStatus,
    error_code: TranslationErrorCode | None = None,
) -> TranslationResult:
    return TranslationResult(
        article_id=article_id,
        target_language="Simplified Chinese",
        paragraphs=paragraphs,
        source_format=TranslationSourceFormat.CLEANED_MARKDOWN,
        generated_at=datetime(2026, 7, 24, 8, 30, tzinfo=UTC),
        provider_model="mock-model",
        status=status,
        is_saved=status is not TranslationStatus.FAILED,
        error_code=error_code,
        error_message="Backend details are not rendered by the UI.",
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


class TranslationPanelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.panels: list[TranslationPanel] = []

    def tearDown(self) -> None:
        for panel in self.panels:
            panel._thread_pool.waitForDone(2000)
            panel.close()
            panel.deleteLater()

    def _panel(self, *args, **kwargs) -> TranslationPanel:
        panel = TranslationPanel(*args, **kwargs)
        self.panels.append(panel)
        return panel

    def _wait_for(self, spy: QSignalSpy) -> None:
        self.assertTrue(wait_for_signal(self.app, spy))

    def test_requires_article_and_routes_missing_generator_to_settings(
        self,
    ) -> None:
        panel = self._panel(Translator("en_US"))

        self.assertFalse(panel.generate_button.isEnabled())
        panel.set_article(translation_source())

        self.assertTrue(panel.generate_button.isEnabled())
        self.assertEqual(panel.language_combo.count(), 2)
        self.assertEqual(
            {
                panel.language_combo.itemData(index)
                for index in range(panel.language_combo.count())
            },
            {"Simplified Chinese", "English"},
        )
        self.assertIn("unavailable", panel.status_label.text())
        self.assertEqual(panel.generate_button.toolTip(), "Open AI settings.")

        settings_spy = QSignalSpy(panel.settings_requested)
        panel.generate_button.click()

        self.assertEqual(settings_spy.count(), 1)

    def test_structured_result_is_emitted_for_reader_rendering(
        self,
    ) -> None:
        calls: list[tuple[TranslationSource, TranslationOptions]] = []
        result = translation_result(
            paragraphs=(
                paragraph(
                    0,
                    "First original.",
                    "第一段译文。",
                    TranslationParagraphStatus.TRANSLATED,
                ),
                paragraph(
                    1,
                    "Second original.",
                    "第二段译文。",
                    TranslationParagraphStatus.TRANSLATED,
                ),
            ),
            status=TranslationStatus.COMPLETED,
        )

        def generate(
            source: TranslationSource,
            options: TranslationOptions,
        ) -> TranslationResult:
            calls.append((source, options))
            return result

        panel = self._panel(Translator("zh_CN"), generator=generate)
        panel.set_article(translation_source())
        panel.prompt_edit.setPlainText("Keep product names unchanged.")
        spy = QSignalSpy(panel.generation_completed)

        panel.generate_button.click()
        self._wait_for(spy)

        self.assertIs(panel.displayed_result, result)
        self.assertEqual(
            panel.displayed_result.paragraphs[0].original_text,
            "First original.",
        )
        self.assertEqual(
            panel.displayed_result.paragraphs[0].translated_text,
            "第一段译文。",
        )
        self.assertEqual(
            panel.displayed_result.paragraphs[1].original_text,
            "Second original.",
        )
        self.assertEqual(
            panel.displayed_result.paragraphs[1].translated_text,
            "第二段译文。",
        )
        self.assertFalse(hasattr(panel, "paragraph_rows"))
        self.assertFalse(hasattr(panel, "comparison_scroll"))
        self.assertIn("Reader 正文", panel.result_location_label.text())
        self.assertEqual(calls[0][1].target_language, "Simplified Chinese")
        self.assertEqual(
            calls[0][1].custom_prompt,
            "Keep product names unchanged.",
        )
        self.assertIn("已完成", panel.status_label.text())

    def test_progressive_result_is_emitted_before_completion(self) -> None:
        progress_result = translation_result(
            paragraphs=(
                paragraph(
                    0,
                    "First original.",
                    "第一段已先显示。",
                    TranslationParagraphStatus.TRANSLATED,
                ),
                paragraph(
                    1,
                    "Second original.",
                    "",
                    TranslationParagraphStatus.PARTIAL,
                ),
            ),
            status=TranslationStatus.PARTIAL,
        )
        completed_result = translation_result(
            paragraphs=(
                paragraph(
                    0,
                    "First original.",
                    "第一段已先显示。",
                    TranslationParagraphStatus.TRANSLATED,
                ),
                paragraph(
                    1,
                    "Second original.",
                    "第二段最终译文。",
                    TranslationParagraphStatus.TRANSLATED,
                ),
            ),
            status=TranslationStatus.COMPLETED,
        )

        def generate(
            _source: TranslationSource,
            _options: TranslationOptions,
            *,
            progress_callback,
        ) -> TranslationResult:
            progress_callback(progress_result)
            return completed_result

        panel = self._panel(Translator("zh_CN"), generator=generate)
        panel.set_article(translation_source())
        progress_spy = QSignalSpy(panel.generation_progress)
        completed_spy = QSignalSpy(panel.generation_completed)

        panel.generate_button.click()
        self._wait_for(completed_spy)

        self.assertEqual(progress_spy.count(), 1)
        emitted_progress = progress_spy.at(0)[0]
        self.assertIs(emitted_progress, progress_result)
        self.assertIs(panel.displayed_result, completed_result)

    def test_failed_paragraph_keeps_original_and_localizes_error(self) -> None:
        result = translation_result(
            paragraphs=(
                paragraph(
                    0,
                    "Translated original.",
                    "已翻译内容。",
                    TranslationParagraphStatus.TRANSLATED,
                ),
                paragraph(
                    1,
                    "Original must stay visible.",
                    "",
                    TranslationParagraphStatus.FAILED,
                    TranslationErrorCode.PROVIDER_FAILURE,
                ),
            ),
            status=TranslationStatus.PARTIAL,
        )
        panel = self._panel(
            Translator("en_US"),
            generator=lambda _source, _options: result,
        )
        panel.set_article(translation_source())
        spy = QSignalSpy(panel.generation_completed)

        panel.generate_button.click()
        self._wait_for(spy)

        displayed = panel.displayed_result
        self.assertIsNotNone(displayed)
        failed_paragraph = displayed.paragraphs[1]
        self.assertEqual(
            failed_paragraph.original_text,
            "Original must stay visible.",
        )
        self.assertEqual(failed_paragraph.translated_text, "")
        self.assertNotIn("Backend details", panel.status_label.text())
        self.assertIn("remains in Reader", panel.status_label.text())

    def test_total_failure_still_displays_every_original(self) -> None:
        result = translation_result(
            paragraphs=(
                paragraph(
                    0,
                    "First retained original.",
                    "",
                    TranslationParagraphStatus.FAILED,
                    TranslationErrorCode.PROVIDER_NOT_CONFIGURED,
                ),
                paragraph(
                    1,
                    "Second retained original.",
                    "",
                    TranslationParagraphStatus.FAILED,
                    TranslationErrorCode.PROVIDER_NOT_CONFIGURED,
                ),
            ),
            status=TranslationStatus.FAILED,
            error_code=TranslationErrorCode.PROVIDER_NOT_CONFIGURED,
        )
        panel = self._panel(
            Translator("en_US"),
            generator=lambda _source, _options: result,
        )
        panel.set_article(translation_source())
        spy = QSignalSpy(panel.generation_completed)

        panel.generate_button.click()
        self._wait_for(spy)

        displayed = panel.displayed_result
        self.assertIsNotNone(displayed)
        self.assertEqual(
            [item.original_text for item in displayed.paragraphs],
            [
                "First retained original.",
                "Second retained original.",
            ],
        )
        self.assertTrue(
            all(
                not item.translated_text
                for item in displayed.paragraphs
            )
        )
        self.assertIn("original remains readable", panel.status_label.text())

    def test_regenerate_replaces_comparison_for_same_article(self) -> None:
        results = [
            translation_result(
                paragraphs=(
                    paragraph(
                        0,
                        "Stable original.",
                        "First translation.",
                        TranslationParagraphStatus.TRANSLATED,
                    ),
                ),
                status=TranslationStatus.COMPLETED,
            ),
            translation_result(
                paragraphs=(
                    paragraph(
                        0,
                        "Stable original.",
                        "Regenerated translation.",
                        TranslationParagraphStatus.TRANSLATED,
                    ),
                ),
                status=TranslationStatus.COMPLETED,
            ),
        ]

        def generate(
            _source: TranslationSource,
            _options: TranslationOptions,
        ) -> TranslationResult:
            return results.pop(0)

        panel = self._panel(Translator("en_US"), generator=generate)
        panel.set_article(translation_source())
        first_spy = QSignalSpy(panel.generation_completed)
        panel.generate_button.click()
        self._wait_for(first_spy)

        self.assertEqual(panel.generate_button.text(), "Translate Again")
        second_spy = QSignalSpy(panel.generation_completed)
        panel.generate_button.click()
        self._wait_for(second_spy)

        self.assertEqual(
            panel.displayed_result.paragraphs[0].translated_text,
            "Regenerated translation.",
        )

    def test_dark_color_scheme_uses_readable_control_text(self) -> None:
        panel = self._panel(Translator("zh_CN"))

        panel.set_color_scheme("dark")

        self.assertEqual(
            panel.prompt_edit.palette()
            .color(QPalette.ColorRole.Text)
            .name(),
            "#f3f6f9",
        )
        self.assertEqual(
            panel.language_combo.palette()
            .color(QPalette.ColorRole.ButtonText)
            .name(),
            "#f3f6f9",
        )

    def test_runtime_language_switch_updates_reader_location_and_status(
        self,
    ) -> None:
        result = translation_result(
            paragraphs=(
                paragraph(
                    0,
                    "Original remains.",
                    "",
                    TranslationParagraphStatus.FAILED,
                    TranslationErrorCode.EMPTY_RESPONSE,
                ),
            ),
            status=TranslationStatus.FAILED,
            error_code=TranslationErrorCode.EMPTY_RESPONSE,
        )
        panel = self._panel(
            Translator("en_US"),
            result_loader=lambda _article_id: result,
        )
        panel.set_article(translation_source())

        panel.set_translator(Translator("zh_CN"))

        self.assertIn("Reader 正文", panel.result_location_label.text())
        self.assertIn("原文仍可阅读", panel.status_label.text())


class TranslationPanelMainWindowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_reader_inline_translation_controls_and_shortcut_preserve_article(
        self,
    ) -> None:
        window = MainWindow(MockArticleService())
        window.show()
        window._show_article("mercury-start")
        self.app.processEvents()

        self.assertEqual(window.reader_splitter.count(), 2)
        self.assertIs(
            window.translation_panel.parentWidget(),
            window.article_reader,
        )
        self.assertEqual(
            window.translation_panel.current_article_id,
            "mercury-start",
        )
        self.assertFalse(window.translation_panel.isVisible())
        self.assertEqual(
            window.toggle_translation_action.shortcut().toString(),
            "Ctrl+Shift+T",
        )

        window.article_reader.translation_toggle_button.click()
        self.app.processEvents()

        self.assertTrue(window.translation_panel.isVisible())
        self.assertTrue(window.toggle_translation_action.isChecked())
        self.assertEqual(
            window.article_reader.current_article_id,
            "mercury-start",
        )

        window.toggle_translation_action.setChecked(False)
        self.app.processEvents()

        self.assertFalse(window.translation_panel.isVisible())
        self.assertFalse(window.toggle_translation_action.isChecked())
        self.assertEqual(
            window.article_reader.current_article_id,
            "mercury-start",
        )
        window.close()
        window.deleteLater()

    def test_reader_displays_translation_progress_without_waiting_for_final(
        self,
    ) -> None:
        window = MainWindow(MockArticleService())
        window.show()
        window._show_article("mercury-start")
        progress_result = translation_result(
            article_id="mercury-start",
            paragraphs=(
                paragraph(
                    0,
                    "Mercury 是一个使用 PySide6 构建的本地优先 RSS 阅读器。",
                    "Mercury is a local-first RSS reader built with PySide6.",
                    TranslationParagraphStatus.TRANSLATED,
                ),
            ),
            status=TranslationStatus.PARTIAL,
        )

        window.translation_panel.generation_progress.emit(progress_result)
        self.app.processEvents()

        rendered = window.article_reader.content.toPlainText()
        self.assertTrue(window.article_reader.bilingual_visible)
        self.assertIn(
            "Mercury is a local-first RSS reader built with PySide6.",
            rendered,
        )
        window.close()
        window.deleteLater()

    def test_reopening_article_restores_last_bilingual_visibility(self) -> None:
        result = translation_result(
            article_id="mercury-start",
            paragraphs=(
                paragraph(
                    0,
                    "Stable original paragraph.",
                    "Stored translated paragraph.",
                    TranslationParagraphStatus.TRANSLATED,
                ),
            ),
            status=TranslationStatus.COMPLETED,
        )
        state_store = InMemoryBilingualViewStateStore()
        window = MainWindow(
            MockArticleService(),
            bilingual_view_state_store=state_store,
            translation_result_loader=(
                lambda article_id: (
                    result if article_id == "mercury-start" else None
                )
            ),
        )
        window.show()
        window._show_article("mercury-start")
        self.app.processEvents()

        self.assertTrue(window.article_reader.bilingual_visible)

        window.article_reader.bilingual_view_button.click()
        self.app.processEvents()

        self.assertFalse(window.article_reader.bilingual_visible)
        self.assertIs(state_store.load("mercury-start"), False)

        window._show_article("pyside-layout")
        window._show_article("mercury-start")
        self.app.processEvents()

        self.assertFalse(window.article_reader.bilingual_visible)
        self.assertFalse(
            window.article_reader.bilingual_view_button.isChecked()
        )
        self.assertNotIn(
            "Stored translated paragraph.",
            window.article_reader.content.toPlainText(),
        )

        window.article_reader.bilingual_view_button.click()
        self.assertIs(state_store.load("mercury-start"), True)
        window.close()
        window.deleteLater()


if __name__ == "__main__":
    unittest.main()
