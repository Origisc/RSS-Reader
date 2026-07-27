import os
import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtWidgets import QApplication

from mercury.domain import (
    TranslationErrorCode,
    TranslationParagraph,
    TranslationParagraphStatus,
    TranslationResult,
    TranslationSourceFormat,
    TranslationStatus,
)
from mercury.models.article import Article
from mercury.ui.article_reader import ArticleReader
from mercury.ui.reader_document import ReaderDocument, ReaderView
from mercury.ui.reader_style import ReaderStyle


class ArticleReaderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.reader = ArticleReader()
        self.reader.set_texts(
            "Reader",
            "Welcome",
            "Choose an article",
            "Source",
            "Local cached content",
        )
        self.reader.set_view_texts(
            raw_label="Original",
            cleaned_html_label="Cleaned HTML",
            markdown_label="Markdown",
            raw_status="Showing original content",
            cleaned_html_status="Showing cleaned HTML",
            markdown_status="Showing cleaned Markdown",
            fallback_unavailable=(
                "{view} is unavailable; showing original content."
            ),
            fallback_error=(
                "Cleaning failed: {error}. Showing original content."
            ),
        )
        self.article = Article(
            id="article-1",
            feed_id="feed-1",
            title="Reader fixture",
            source_title="Local fixture",
            content_html="<p>First-stage original</p>",
        )

    def tearDown(self) -> None:
        self.reader.close()
        self.reader.deleteLater()

    def test_switches_between_structured_reader_views(self) -> None:
        document = ReaderDocument(
            raw_html="<p>Raw unique text</p>",
            cleaned_html="<article><p>Clean HTML unique text</p></article>",
            cleaned_markdown="## Markdown unique text\n\n- one\n- two",
        )
        self.reader.show_article(self.article, document)

        self.reader.set_view(ReaderView.CLEANED_HTML)
        self.assertIn("Clean HTML unique text", self.reader.content.toPlainText())
        self.assertNotIn("Raw unique text", self.reader.content.toPlainText())

        self.reader.set_view(ReaderView.MARKDOWN)
        markdown_text = self.reader.content.toPlainText()
        self.assertIn("Markdown unique text", markdown_text)
        self.assertIn("one", markdown_text)
        self.assertEqual(self.reader.current_article_id, "article-1")

    def test_markdown_view_uses_dark_reader_text_color(self) -> None:
        document = ReaderDocument(
            raw_html="<p>Raw fallback</p>",
            cleaned_markdown=(
                "## Visible heading\n\n"
                "First visible paragraph.\n\n"
                "Second visible paragraph."
            ),
        )
        self.reader.show_article(self.article, document)

        self.reader.set_view(ReaderView.MARKDOWN)

        rendered_html = self.reader.content.toHtml().replace(" ", "").lower()
        rendered_text = self.reader.content.toPlainText()
        markdown_fragment = self.reader._markdown_fragment(
            document.cleaned_markdown or ""
        )
        self.assertIn("First visible paragraph", rendered_text)
        self.assertIn("Second visible paragraph", rendered_text)
        self.assertGreaterEqual(markdown_fragment.lower().count("<p"), 2)
        self.assertIn("color:#d7e3ed", rendered_html)

    def test_cleaning_failure_keeps_original_article_readable(self) -> None:
        document = ReaderDocument(
            raw_html="<p>Readable fallback text</p>",
            cleaning_error="fixture cleaner failed",
        )
        self.reader.show_article(self.article, document)

        self.reader.set_view(ReaderView.CLEANED_HTML)

        self.assertEqual(self.reader.current_view, ReaderView.CLEANED_HTML)
        self.assertIn("Readable fallback text", self.reader.content.toPlainText())
        self.assertIn("fixture cleaner failed", self.reader.view_status_label.text())
        self.assertEqual(self.reader.current_article_id, "article-1")

    def test_first_stage_article_uses_original_content_fallback(self) -> None:
        self.reader.show_article(self.article)

        self.reader.set_view(ReaderView.MARKDOWN)

        self.assertIn("First-stage original", self.reader.content.toPlainText())
        self.assertIn("unavailable", self.reader.view_status_label.text())

    def test_document_keeps_feed_content_as_original_view(self) -> None:
        article = Article(
            id="processed-article",
            feed_id="feed-1",
            title="Processed fixture",
            source_title="Local fixture",
            content_html="<p>Feed summary</p>",
            original_html="<article><p>Fetched original</p></article>",
            cleaned_html="<article><p>Cleaned result</p></article>",
            cleaned_markdown="## Cleaned Markdown",
            clean_error="previous cleaning warning",
        )

        document = ReaderDocument.from_article(article)

        self.assertIn("Feed summary", document.raw_html)
        self.assertNotIn("Fetched original", document.raw_html)
        self.assertIn("Cleaned result", document.cleaned_html or "")
        self.assertEqual(document.cleaned_markdown, "## Cleaned Markdown")
        self.assertEqual(document.cleaning_error, "previous cleaning warning")

    def test_document_uses_fetched_html_when_feed_content_is_empty(self) -> None:
        article = Article(
            id="fetched-only",
            feed_id="feed-1",
            title="Fetched-only fixture",
            source_title="Local fixture",
            content_html="",
            original_html="<article><p>Fetched fallback</p></article>",
        )

        document = ReaderDocument.from_article(article)

        self.assertIn("Fetched fallback", document.raw_html)

    def test_reader_style_is_applied_without_changing_article(self) -> None:
        self.reader.show_article(self.article)
        style = ReaderStyle(
            font_size=24,
            line_height=2.0,
            content_width=640,
        )

        self.reader.set_reader_style(style)
        rendered_html = self.reader._wrap_html("<p>Styled content</p>")

        self.assertEqual(self.reader.reader_style, style)
        self.assertEqual(self.reader.current_article_id, "article-1")
        self.assertIn("font-size: 24px", rendered_html)
        self.assertIn("line-height: 2.0", rendered_html)
        self.assertIn("max-width: 640px", rendered_html)

    def test_translation_is_interleaved_in_reader_and_can_return_to_original(
        self,
    ) -> None:
        document = ReaderDocument(
            raw_html="<p>Raw reader body.</p>",
            cleaned_markdown="First original.\n\nSecond original.",
        )
        self.reader.show_article(self.article, document)
        result = self._translation_result(
            (
                self._paragraph(0, "First original.", "第一段译文。"),
                self._paragraph(1, "Second original.", "第二段译文。"),
            )
        )

        self.reader.set_translation_result(result)

        rendered = self.reader.content.toPlainText()
        self.assertTrue(self.reader.bilingual_visible)
        self.assertTrue(self.reader.bilingual_view_button.isChecked())
        self.assertEqual(
            self.reader.bilingual_view_button.text(),
            "Original only",
        )
        self.assertLess(
            rendered.index("First original."),
            rendered.index("第一段译文。"),
        )
        self.assertLess(
            rendered.index("第一段译文。"),
            rendered.index("Second original."),
        )
        self.assertLess(
            rendered.index("Second original."),
            rendered.index("第二段译文。"),
        )
        self.assertTrue(
            all(
                not button.isEnabled()
                for button in self.reader.view_buttons.values()
            )
        )

        self.reader.bilingual_view_button.click()

        original_only = self.reader.content.toPlainText()
        self.assertFalse(self.reader.bilingual_visible)
        self.assertIn("Raw reader body.", original_only)
        self.assertNotIn("第一段译文。", original_only)
        self.assertTrue(
            all(
                button.isEnabled()
                for button in self.reader.view_buttons.values()
            )
        )

    def test_failed_translation_keeps_original_in_reader(self) -> None:
        document = ReaderDocument(
            raw_html="<p>Fallback body.</p>",
            cleaned_markdown=(
                "Translated original.\n\nOriginal must stay visible."
            ),
        )
        self.reader.show_article(self.article, document)
        self.reader.set_translation_view_texts(
            show_bilingual="双语对照",
            show_original="显示原文",
            available_tooltip="切换",
            unavailable_tooltip="请先翻译",
            status="双语模式",
            translation_unavailable="译文暂不可用",
            translation_translating="正在翻译...",
        )
        result = self._translation_result(
            (
                self._paragraph(
                    0,
                    "Translated original.",
                    "已有译文。",
                ),
                self._paragraph(
                    1,
                    "Original must stay visible.",
                    "",
                    status=TranslationParagraphStatus.FAILED,
                    error_code=TranslationErrorCode.PROVIDER_FAILURE,
                ),
            ),
            status=TranslationStatus.PARTIAL,
        )

        self.reader.set_translation_result(result)

        rendered = self.reader.content.toPlainText()
        self.assertIn("Original must stay visible.", rendered)
        self.assertIn("译文暂不可用", rendered)
        self.assertLess(
            rendered.index("Original must stay visible."),
            rendered.index("译文暂不可用"),
        )

    def test_bilingual_markdown_preserves_links_and_images(self) -> None:
        original = (
            "[Example link](https://example.com/article) "
            "![Diagram](https://example.com/diagram.png)"
        )
        self.reader.show_article(
            self.article,
            ReaderDocument(
                raw_html="<p>Raw fallback.</p>",
                cleaned_markdown=original,
            ),
        )

        self.reader.set_translation_result(
            self._translation_result(
                (self._paragraph(0, original, "示例链接与图片。"),)
            )
        )

        rendered_html = self.reader.content.toHtml()
        self.assertIn("https://example.com/article", rendered_html)
        self.assertIn("https://example.com/diagram.png", rendered_html)
        self.assertIn("示例链接与图片", self.reader.content.toPlainText())

    def test_bilingual_raw_html_preserves_original_blocks_and_interleaves(
        self,
    ) -> None:
        source_html = (
            '<p>First <strong>bold</strong> '
            '<a href="https://example.com/one">paragraph</a>.</p>'
            "<blockquote><p>Second quoted paragraph.</p></blockquote>"
            "<ul><li>Third list item.</li></ul>"
            '<img src="https://example.com/original.png" alt="Original">'
        )
        self.reader.show_article(
            self.article,
            ReaderDocument(raw_html=source_html),
        )
        result = self._translation_result(
            (
                self._paragraph(
                    0,
                    "First bold paragraph.",
                    "第一段译文。",
                ),
                self._paragraph(
                    1,
                    "Second quoted paragraph.",
                    "第二段译文。",
                ),
                self._paragraph(
                    2,
                    "Third list item.",
                    "第三段译文。",
                ),
            ),
            source_format=TranslationSourceFormat.RAW_HTML,
        )

        self.reader.set_translation_result(result)

        rendered = self.reader.content.toPlainText()
        rendered_html = self.reader.content.toHtml()
        self.assertLess(
            rendered.index("First bold paragraph."),
            rendered.index("第一段译文。"),
        )
        self.assertLess(
            rendered.index("第一段译文。"),
            rendered.index("Second quoted paragraph."),
        )
        self.assertLess(
            rendered.index("Second quoted paragraph."),
            rendered.index("第二段译文。"),
        )
        self.assertLess(
            rendered.index("第二段译文。"),
            rendered.index("Third list item."),
        )
        self.assertLess(
            rendered.index("Third list item."),
            rendered.index("第三段译文。"),
        )
        self.assertIn("https://example.com/one", rendered_html)
        self.assertIn("https://example.com/original.png", rendered_html)
        self.assertIn("font-weight:700", rendered_html.replace(" ", ""))

    def test_bilingual_legacy_br_fragment_uses_structured_pairs(
        self,
    ) -> None:
        self.reader.show_article(
            self.article,
            ReaderDocument(
                raw_html=(
                    "First legacy paragraph.<br><br>"
                    "Second legacy paragraph."
                ),
            ),
        )
        result = self._translation_result(
            (
                self._paragraph(
                    0,
                    "First legacy paragraph.",
                    "第一段旧式译文。",
                ),
                self._paragraph(
                    1,
                    "Second legacy paragraph.",
                    "第二段旧式译文。",
                ),
            ),
            source_format=TranslationSourceFormat.RAW_HTML,
        )

        self.reader.set_translation_result(result)

        rendered = self.reader.content.toPlainText()
        self.assertLess(
            rendered.index("First legacy paragraph."),
            rendered.index("第一段旧式译文。"),
        )
        self.assertLess(
            rendered.index("第一段旧式译文。"),
            rendered.index("Second legacy paragraph."),
        )
        self.assertLess(
            rendered.index("Second legacy paragraph."),
            rendered.index("第二段旧式译文。"),
        )

    @staticmethod
    def _paragraph(
        index: int,
        original: str,
        translated: str,
        *,
        status: TranslationParagraphStatus = (
            TranslationParagraphStatus.TRANSLATED
        ),
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
        )

    def _translation_result(
        self,
        paragraphs: tuple[TranslationParagraph, ...],
        *,
        status: TranslationStatus = TranslationStatus.COMPLETED,
        source_format: TranslationSourceFormat = (
            TranslationSourceFormat.CLEANED_MARKDOWN
        ),
    ) -> TranslationResult:
        return TranslationResult(
            article_id=self.article.id,
            target_language="Simplified Chinese",
            paragraphs=paragraphs,
            source_format=source_format,
            generated_at=datetime(2026, 7, 24, tzinfo=UTC),
            provider_model="mock-model",
            status=status,
        )


if __name__ == "__main__":
    unittest.main()
