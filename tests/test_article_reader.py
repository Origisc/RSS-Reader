import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtWidgets import QApplication

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

    def test_document_uses_persisted_processing_results(self) -> None:
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

        self.assertIn("Fetched original", document.raw_html)
        self.assertIn("Cleaned result", document.cleaned_html or "")
        self.assertEqual(document.cleaned_markdown, "## Cleaned Markdown")
        self.assertEqual(document.cleaning_error, "previous cleaning warning")

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


if __name__ == "__main__":
    unittest.main()
