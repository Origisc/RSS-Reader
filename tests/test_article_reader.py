import os
import sys
import unittest
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QUrl
from PySide6.QtGui import QFont, QImage, QTextDocument
from PySide6.QtNetwork import QNetworkReply, QNetworkRequest
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
from mercury.ui.article_reader import ArticleReader, _ResolvedImage
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
            link="https://example.com/articles/reader-fixture/",
        )

    def tearDown(self) -> None:
        self.reader.close()
        self.reader.deleteLater()

    def test_reader_keeps_original_title_when_entry_title_is_translated(
        self,
    ) -> None:
        self.reader.show_article(
            replace(
                self.article,
                translated_title="已翻译标题",
            )
        )

        reader_text = self.reader.content.toPlainText()
        self.assertIn("Reader fixture", reader_text)
        self.assertNotIn("已翻译标题", reader_text)

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
        self.assertIn("color:#e8e3da", rendered_html)

    def test_source_page_styles_cannot_override_dark_reader_theme(self) -> None:
        source_page = """
            <!doctype html>
            <html bgcolor="#ffffff">
            <head>
                <style>
                    body, .source-shell {
                        background: #ffffff;
                        color: #111111;
                    }
                </style>
                <script>window.sourceApp = true;</script>
            </head>
            <body>
                <div class="source-shell"
                     style="background-color: white; color: black;
                            text-align: center;">
                    <p>Theme-safe original article.</p>
                </div>
            </body>
            </html>
        """

        self.reader.show_article(
            self.article,
            ReaderDocument(raw_html=source_page),
        )

        rendered_html = self.reader.content.toHtml().replace(" ", "").lower()
        rendered_text = self.reader.content.toPlainText()
        safe_fragment = ReaderDocument.prepare_for_embedding(source_page)

        self.assertIn("Theme-safe original article", rendered_text)
        self.assertIn('bgcolor="#191b1f"', rendered_html)
        self.assertNotIn("<head", safe_fragment.lower())
        self.assertNotIn("<style", safe_fragment.lower())
        self.assertNotIn("<script", safe_fragment.lower())
        self.assertNotIn("background-color:white", safe_fragment.lower())
        self.assertNotIn("color:black", safe_fragment.lower())
        self.assertIn("text-align: center", safe_fragment.lower())

    def test_light_theme_renders_reader_as_a_light_paper_surface(self) -> None:
        self.reader.set_color_scheme("light")
        self.reader.show_article(
            self.article,
            ReaderDocument(
                raw_html="<p>Readable light content.</p>",
            ),
        )

        rendered_html = self.reader.content.toHtml().replace(" ", "").lower()

        self.assertIn('bgcolor="#ffffff"', rendered_html)
        self.assertIn("color:#202124", rendered_html)
        self.assertIn("Readable light content", self.reader.content.toPlainText())

    def test_markdown_view_preserves_structural_formatting(self) -> None:
        document = ReaderDocument(
            raw_html="<p>Raw fallback</p>",
            cleaned_markdown=(
                "## Structured heading\n\n"
                "- First list item with **Bold marker**\n"
                "- Second list item with *Italic marker*\n\n"
                "Use `inline_code()` here.\n\n"
                "```python\n"
                "print('fenced code')\n"
                "```"
            ),
        )
        self.reader.show_article(self.article, document)

        self.reader.set_view(ReaderView.MARKDOWN)

        rendered = self.reader.content.document()
        blocks = []
        block = rendered.begin()
        while block.isValid():
            blocks.append(block)
            block = block.next()

        heading = next(
            block for block in blocks
            if block.text() == "Structured heading"
        )
        first_list_item = next(
            block for block in blocks
            if block.text().startswith("First list item")
        )
        second_list_item = next(
            block for block in blocks
            if block.text().startswith("Second list item")
        )

        self.assertEqual(heading.blockFormat().headingLevel(), 2)
        self.assertIsNotNone(first_list_item.textList())
        self.assertIs(first_list_item.textList(), second_list_item.textList())

        formats = {}
        for block in blocks:
            iterator = block.begin()
            while not iterator.atEnd():
                fragment = iterator.fragment()
                if fragment.isValid():
                    formats[fragment.text()] = fragment.charFormat()
                iterator += 1

        bold_format = next(
            char_format
            for text, char_format in formats.items()
            if "Bold marker" in text
        )
        italic_format = next(
            char_format
            for text, char_format in formats.items()
            if "Italic marker" in text
        )
        inline_code_format = next(
            char_format
            for text, char_format in formats.items()
            if "inline_code()" in text
        )
        fenced_code_format = next(
            char_format
            for text, char_format in formats.items()
            if "fenced code" in text
        )

        self.assertGreaterEqual(
            bold_format.fontWeight(),
            QFont.Weight.Bold,
        )
        self.assertTrue(italic_format.fontItalic())
        self.assertIn("monospace", inline_code_format.fontFamilies())
        self.assertIn("monospace", fenced_code_format.fontFamilies())

    def test_markdown_paragraph_gap_exceeds_intra_paragraph_line_height(
        self,
    ) -> None:
        style = ReaderStyle(
            font_size=20,
            line_height=1.5,
            content_width=700,
        )
        document = ReaderDocument(
            raw_html="<p>Raw fallback</p>",
            cleaned_markdown=(
                "First paragraph has a first line.\n"
                "It continues inside the same paragraph.\n\n"
                "Second paragraph starts after a larger gap."
            ),
        )
        self.reader.set_reader_style(style)
        self.reader.show_article(self.article, document)

        fragment = self.reader._markdown_fragment(
            document.cleaned_markdown or ""
        )
        normalized_fragment = fragment.replace(" ", "").lower()
        self.assertNotIn("margin-top:0px", normalized_fragment)
        self.assertNotIn("margin-bottom:0px", normalized_fragment)

        self.reader.set_view(ReaderView.MARKDOWN)

        first_paragraph = self.reader.content.document().begin()
        while (
            first_paragraph.isValid()
            and not first_paragraph.text().startswith(
                "First paragraph has a first line."
            )
        ):
            first_paragraph = first_paragraph.next()

        self.assertTrue(first_paragraph.isValid())
        paragraph_gap = first_paragraph.blockFormat().bottomMargin()
        line_box_height = style.font_size * style.line_height
        self.assertGreater(paragraph_gap, line_box_height)
        self.assertAlmostEqual(
            paragraph_gap,
            style.paragraph_spacing_px,
            delta=0.5,
        )

    def test_resolved_markdown_image_uses_matching_scaled_dimensions(
        self,
    ) -> None:
        self.reader.set_reader_style(
            ReaderStyle(
                font_size=18,
                line_height=1.6,
                content_width=700,
            )
        )
        width, height = self.reader._scaled_image_size(840, 583)
        fragment = (
            '<p><img src="https://example.com/image.jpg" '
            'width="840" height="583" alt="Fixture"></p>'
            "<h1>Heading immediately after the image</h1>"
        )

        resolved = self.reader._replace_resolved_images(
            fragment,
            {
                "https://example.com/image.jpg": _ResolvedImage(
                    data_url="data:image/jpeg;base64,fixture",
                    width=width,
                    height=height,
                )
            },
        )

        self.assertEqual((width, height), (700, 486))
        self.assertIn('width="700"', resolved)
        self.assertIn('height="486"', resolved)
        self.assertIn("line-height:100%", resolved)
        self.assertNotIn('width="840"', resolved)
        self.assertNotIn('height="583"', resolved)
        self.assertLess(
            resolved.index('height="486"'),
            resolved.index("Heading immediately after the image"),
        )

        rendered = QTextDocument()
        rendered.setHtml(
            self.reader._wrap_html(
                f'<div class="reader-article">{resolved}</div>'
            )
        )
        image_block = rendered.begin()
        while image_block.isValid() and "\ufffc" not in image_block.text():
            image_block = image_block.next()
        heading_block = image_block.next()

        self.assertTrue(image_block.isValid())
        self.assertTrue(heading_block.isValid())
        self.assertIn("Heading immediately", heading_block.text())
        image_rect = rendered.documentLayout().blockBoundingRect(image_block)
        heading_rect = rendered.documentLayout().blockBoundingRect(heading_block)
        gap_after_image = heading_rect.top() - image_rect.bottom()
        self.assertLessEqual(
            gap_after_image,
            self.reader.reader_style.paragraph_spacing_px + 0.5,
        )

    def test_small_resolved_image_is_not_upscaled(self) -> None:
        self.reader.set_reader_style(ReaderStyle(content_width=820))

        self.assertEqual(
            self.reader._scaled_image_size(320, 180),
            (320, 180),
        )

    def test_image_width_tracks_narrow_reader_viewport(self) -> None:
        self.reader.show()
        self.reader.resize(560, 720)
        self.app.processEvents()

        width, height = self.reader._scaled_image_size(1200, 600)
        available_width = max(
            120,
            self.reader.content.viewport().width() - 108,
        )

        self.assertLessEqual(width, available_width)
        self.assertEqual(height, round(width / 2))

    def test_link_only_404_entry_shows_clear_issue_and_keeps_link(self) -> None:
        link = "https://example.com/removed-article"
        article = replace(
            self.article,
            content_html=f'<p><a href="{link}">{link}</a></p>',
            fetch_status="failed",
            fetch_error="HTTP error: 404 Client Error: Not Found",
        )
        self.reader.set_content_issue_texts(
            link_only_loading="Loading linked article.",
            link_only_not_found="The linked article returned 404.",
            link_only_failed="Loading failed: {error}",
            link_only_available="Full content is available.",
        )

        self.reader.show_article(article)

        rendered_text = self.reader.content.toPlainText()
        self.assertIn("The linked article returned 404.", rendered_text)
        self.assertIn(link, rendered_text)
        self.assertNotIn("Loading linked article.", rendered_text)

    def test_link_only_entry_reports_background_loading(self) -> None:
        link = "https://example.com/pending-article"
        article = replace(
            self.article,
            content_html=f'<p><a href="{link}">{link}</a></p>',
            fetch_status="pending",
        )
        self.reader.set_content_issue_texts(
            link_only_loading="Loading linked article.",
            link_only_not_found="The linked article returned 404.",
            link_only_failed="Loading failed: {error}",
            link_only_available="Full content is available.",
        )

        self.reader.show_article(article)

        self.assertIn(
            "Loading linked article.",
            self.reader.content.toPlainText(),
        )

    def test_image_only_figure_does_not_reserve_scaled_line_height(
        self,
    ) -> None:
        fragment = (
            '<figure class="insert-image">'
            '<img alt="Fixture" height="auto" '
            'src="https://example.com/figure.jpg" width="700" />'
            "</figure>"
            "<p>Text immediately after the figure.</p>"
        )
        resolved = self.reader._replace_resolved_images(
            fragment,
            {
                "https://example.com/figure.jpg": _ResolvedImage(
                    data_url="data:image/jpeg;base64,fixture",
                    width=700,
                    height=350,
                )
            },
        )

        self.assertNotIn("<figure", resolved)
        self.assertIn("<p", resolved)
        self.assertIn("line-height:100%", resolved)
        self.assertNotIn('height="auto"', resolved)

        rendered = QTextDocument()
        rendered.setHtml(
            self.reader._wrap_html(
                f'<div class="reader-article">{resolved}</div>'
            )
        )
        image_block = rendered.begin()
        while image_block.isValid() and "\ufffc" not in image_block.text():
            image_block = image_block.next()
        text_block = image_block.next()

        self.assertTrue(image_block.isValid())
        self.assertTrue(text_block.isValid())
        self.assertIn("Text immediately", text_block.text())
        image_rect = rendered.documentLayout().blockBoundingRect(image_block)
        text_rect = rendered.documentLayout().blockBoundingRect(text_block)
        self.assertLessEqual(
            text_rect.top() - image_rect.bottom(),
            self.reader.reader_style.paragraph_spacing_px + 0.5,
        )

    def test_bare_image_after_translation_uses_its_own_media_block(
        self,
    ) -> None:
        image_url = "https://example.com/bilingual-bare-image.jpg"
        fragment = (
            "<p>Original paragraph.</p>"
            '<div class="translation-block"><p>译文段落。</p></div>'
            f'<img src="{image_url}" width="700" height="auto">'
            "<p>Text immediately after the image.</p>"
        )
        resolved = self.reader._replace_resolved_images(
            fragment,
            {
                image_url: _ResolvedImage(
                    data_url="data:image/jpeg;base64,fixture",
                    width=700,
                    height=420,
                )
            },
        )

        self.assertIn(
            '<p style="line-height:100%;"><img',
            resolved,
        )
        self.assertNotIn('height="auto"', resolved)

        rendered = QTextDocument()
        rendered.setTextWidth(840)
        rendered.setHtml(
            self.reader._wrap_html(
                f'<div class="reader-article bilingual-article">'
                f"{resolved}</div>"
            )
        )
        image_block = rendered.begin()
        while image_block.isValid() and "\ufffc" not in image_block.text():
            image_block = image_block.next()
        text_block = image_block.next()
        while (
            text_block.isValid()
            and "Text immediately" not in text_block.text()
        ):
            text_block = text_block.next()

        self.assertTrue(image_block.isValid())
        self.assertTrue(text_block.isValid())
        self.assertEqual(image_block.text(), "\ufffc")
        layout = rendered.documentLayout()
        image_rect = layout.blockBoundingRect(image_block)
        text_rect = layout.blockBoundingRect(text_block)
        self.assertLessEqual(image_rect.height(), 420.5)
        self.assertLessEqual(
            text_rect.top() - image_rect.bottom(),
            self.reader.reader_style.paragraph_spacing_px + 0.5,
        )

    def test_wordpress_image_caption_does_not_scale_image_line_height(
        self,
    ) -> None:
        image_url = "https://example.com/wordpress-caption.png"
        fragment = (
            '<div class="article-body">'
            "<p>Paragraph before the image.</p>"
            '<div class="wp-caption" style="width: 760px;">'
            '<img aria-describedby="caption-fixture" '
            f'src="{image_url}" width="750" height="421"></img>'
            '<p class="wp-caption-text" id="caption-fixture">'
            "Image caption from the article source."
            "</p></div>"
            "<p>Paragraph immediately after the caption.</p>"
            "</div>"
        )
        resolved = self.reader._replace_resolved_images(
            fragment,
            {
                image_url: _ResolvedImage(
                    data_url="data:image/png;base64,fixture",
                    width=750,
                    height=421,
                )
            },
        )

        self.assertIn("<div", resolved)
        self.assertIn("line-height:100%", resolved)
        self.assertIn("line-height:normal", resolved)
        self.assertNotIn("width: 760px", resolved)

        rendered = QTextDocument()
        rendered.setHtml(
            self.reader._wrap_html(
                f'<div class="reader-article">{resolved}</div>'
            )
        )
        image_block = rendered.begin()
        while image_block.isValid() and "\ufffc" not in image_block.text():
            image_block = image_block.next()
        caption_block = image_block.next()
        while (
            caption_block.isValid()
            and "Image caption" not in caption_block.text()
        ):
            caption_block = caption_block.next()
        next_block = caption_block.next()
        while (
            next_block.isValid()
            and "Paragraph immediately" not in next_block.text()
        ):
            next_block = next_block.next()

        self.assertTrue(image_block.isValid())
        self.assertTrue(caption_block.isValid())
        self.assertTrue(next_block.isValid())
        layout = rendered.documentLayout()
        image_rect = layout.blockBoundingRect(image_block)
        caption_rect = layout.blockBoundingRect(caption_block)
        next_rect = layout.blockBoundingRect(next_block)
        self.assertLessEqual(
            caption_rect.top() - image_rect.bottom(),
            self.reader.reader_style.paragraph_spacing_px + 0.5,
        )
        self.assertLessEqual(
            next_rect.top() - caption_rect.bottom(),
            self.reader.reader_style.paragraph_spacing_px + 0.5,
        )

    def test_wordpress_caption_cannot_force_narrow_reader_to_overflow(
        self,
    ) -> None:
        self.reader.show()
        self.reader.resize(560, 720)
        self.app.processEvents()
        image_url = (
            "https://krebsonsecurity.com/wp-content/uploads/"
            "2025/09/rocketace-tmobile.png"
        )
        fragment = (
            '<div class="wp-caption aligncenter" width="819" '
            'style="margin: 0 auto; width: 819px; max-width: 100%; '
            'height: 915px; border: 1px solid transparent;">'
            f'<img src="{image_url}" width="809" height="915">'
            '<p class="wp-caption-text">KrebsOnSecurity caption.</p>'
            "</div>"
        )

        resolved = self.reader._replace_resolved_images(
            fragment,
            {},
        )
        expected_width, expected_height = self.reader._scaled_image_size(
            809,
            915,
        )

        self.assertNotIn('width="819"', resolved)
        self.assertNotIn("width: 819px", resolved)
        self.assertNotIn("max-width: 100%", resolved)
        self.assertNotIn("height: 915px", resolved)
        self.assertIn("margin: 0 auto", resolved)
        self.assertIn("border: 1px solid transparent", resolved)
        self.assertIn(f'width="{expected_width}"', resolved)
        self.assertIn(f'height="{expected_height}"', resolved)
        self.assertLessEqual(
            expected_width,
            self.reader._image_max_width(),
        )

    def test_linked_picture_wrapper_is_treated_as_image_only_block(
        self,
    ) -> None:
        image_url = "https://example.com/linked-picture.png"
        fragment = (
            '<div class="responsive-image">'
            '<a href="https://example.com/full-size">'
            "<picture>"
            '<source srcset="fixture-small.png">'
            f'<img src="{image_url}" alt="Fixture">'
            "</picture>"
            "</a>"
            "</div>"
            "<p>Text after linked picture.</p>"
        )
        resolved = self.reader._replace_resolved_images(
            fragment,
            {
                image_url: _ResolvedImage(
                    data_url="data:image/png;base64,fixture",
                    width=640,
                    height=360,
                )
            },
        )

        self.assertTrue(resolved.startswith("<p"))
        self.assertIn("line-height:100%", resolved)

        rendered = QTextDocument()
        rendered.setHtml(
            self.reader._wrap_html(
                f'<div class="reader-article">{resolved}</div>'
            )
        )
        image_block = rendered.begin()
        while image_block.isValid() and "\ufffc" not in image_block.text():
            image_block = image_block.next()
        text_block = image_block.next()
        while (
            text_block.isValid()
            and "Text after linked picture" not in text_block.text()
        ):
            text_block = text_block.next()

        self.assertTrue(image_block.isValid())
        self.assertTrue(text_block.isValid())
        image_rect = rendered.documentLayout().blockBoundingRect(image_block)
        text_rect = rendered.documentLayout().blockBoundingRect(text_block)
        self.assertLessEqual(
            text_rect.top() - image_rect.bottom(),
            self.reader.reader_style.paragraph_spacing_px + 0.5,
        )

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

    def test_document_keeps_feed_content_before_successful_fetch(self) -> None:
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

    def test_document_uses_complete_fetch_when_feed_is_only_excerpt(
        self,
    ) -> None:
        complete_body = " ".join(
            f"<p>Complete article paragraph {index}.</p>"
            for index in range(30)
        )
        article = Article(
            id="complete-fetch",
            feed_id="feed-1",
            title="Complete fetch fixture",
            source_title="Local fixture",
            content_html="<p>Short Feed excerpt.</p>",
            original_html=(
                "<html><body><article>"
                f"{complete_body}"
                "<h2>Conclusion marker</h2>"
                "</article></body></html>"
            ),
            fetched_at="2026-07-30T10:00:00",
            fetch_status="success",
        )

        document = ReaderDocument.from_article(article)

        self.assertIn("Complete article paragraph 29", document.raw_html)
        self.assertIn("Conclusion marker", document.raw_html)
        self.assertNotIn("Short Feed excerpt", document.raw_html)

    def test_complete_page_uses_clean_article_without_site_shell(self) -> None:
        complete_body = " ".join(
            f"<p>Full safe paragraph {index}.</p>"
            for index in range(20)
        )
        cleaned_html = (
            "<article>"
            f"{complete_body}"
            "<h2>Safe conclusion marker</h2>"
            "</article>"
        )
        article = Article(
            id="complete-page-shell",
            feed_id="feed-1",
            title="Complete page shell fixture",
            source_title="Local fixture",
            content_html="<p>Short Feed excerpt.</p>",
            original_html=(
                "<!doctype html><html><head>"
                "<style>body { background: white; color: black; }</style>"
                "</head><body>"
                "<header>Source navigation and advertisement</header>"
                f"<main>{cleaned_html}</main>"
                "<aside>Unrelated source sidebar</aside>"
                "</body></html>"
            ),
            cleaned_html=cleaned_html,
            fetched_at="2026-07-30T10:00:00",
            fetch_status="success",
        )

        document = ReaderDocument.from_article(article)

        self.assertEqual(document.raw_html, cleaned_html)
        self.assertIn("Full safe paragraph 19", document.raw_html)
        self.assertIn("Safe conclusion marker", document.raw_html)
        self.assertNotIn("background: white", document.raw_html)
        self.assertNotIn("Source navigation", document.raw_html)
        self.assertNotIn("Unrelated source sidebar", document.raw_html)

    def test_document_keeps_feed_when_successful_fetch_is_short_shell(
        self,
    ) -> None:
        feed_body = " ".join(
            f"<p>Useful Feed paragraph {index}.</p>"
            for index in range(20)
        )
        article = Article(
            id="short-shell",
            feed_id="feed-1",
            title="Short shell fixture",
            source_title="Local fixture",
            content_html=feed_body,
            original_html=(
                "<html><body>"
                f"<script>{'x' * 5000}</script>"
                "<p>Please enable JavaScript.</p>"
                "</body></html>"
            ),
            fetched_at="2026-07-30T10:00:00",
            fetch_status="success",
        )

        document = ReaderDocument.from_article(article)

        self.assertIn("Useful Feed paragraph 19", document.raw_html)
        self.assertNotIn("Please enable JavaScript", document.raw_html)

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

    def test_bilingual_view_reuses_resolved_image_cache(self) -> None:
        image_url = "https://example.com/resolved.png"
        source_html = (
            "<p>Original paragraph.</p>"
            f'<figure><img src="{image_url}" alt="Resolved"></figure>'
        )
        self.reader._resolve_images_async = lambda _html: None
        self.reader.show_article(
            self.article,
            ReaderDocument(raw_html=source_html),
        )
        self.reader._image_replacements[image_url] = _ResolvedImage(
            data_url="data:image/png;base64,fixture",
            width=900,
            height=450,
            natural_width=900,
            natural_height=450,
        )

        self.reader.set_translation_result(
            self._translation_result(
                (
                    self._paragraph(
                        0,
                        "Original paragraph.",
                        "原文段落译文。",
                    ),
                ),
                source_format=TranslationSourceFormat.RAW_HTML,
            )
        )

        rendered_html = self.reader.content.toHtml()
        self.assertIn("data:image/png;base64,fixture", rendered_html)
        self.assertNotIn(image_url, rendered_html)
        self.assertIn("原文段落译文", self.reader.content.toPlainText())

    def test_translation_toggle_reuses_qt_resource_without_network(
        self,
    ) -> None:
        image_url = "https://example.com/toggle-resource.png"
        source_html = (
            "<p>Original paragraph.</p>"
            f'<img src="{image_url}" alt="Cached resource">'
        )

        class NoNetworkManager:
            def __init__(self) -> None:
                self.request_count = 0

            def get(self, _request):
                self.request_count += 1
                raise AssertionError("A cached image must not be requested.")

        image = QImage(320, 180, QImage.Format.Format_RGB32)
        image.fill(0xFF336699)
        resource_url = self.reader._image_resource_url(image_url)
        manager = NoNetworkManager()
        self.reader._current_article = self.article
        self.reader._current_document = ReaderDocument(raw_html=source_html)
        self.reader._network_manager = manager
        self.reader._image_replacements[image_url] = _ResolvedImage(
            data_url="",
            width=320,
            height=180,
            natural_width=320,
            natural_height=180,
            resource_url=resource_url,
            image=image,
        )

        self.reader._render_current_view()
        self.reader.set_translation_result(
            self._translation_result(
                (
                    self._paragraph(
                        0,
                        "Original paragraph.",
                        "原文段落译文。",
                    ),
                ),
                source_format=TranslationSourceFormat.RAW_HTML,
            )
        )
        for _ in range(3):
            self.reader.set_bilingual_visible(False)
            self.reader.set_bilingual_visible(True)

        rendered_html = self.reader.content.toHtml()
        self.assertEqual(manager.request_count, 0)
        self.assertIn(resource_url, rendered_html)
        self.assertNotIn("base64", rendered_html)
        self.assertIn("原文段落译文", self.reader.content.toPlainText())

    def test_bilingual_view_reuses_absolute_cache_for_relative_image(
        self,
    ) -> None:
        article_url = (
            "https://www.jeffgeerling.com/blog/2026/"
            "build-your-own-dial-up-isp-with-a-raspberry-pi/"
        )
        relative_url = (
            "/blog/2026/build-your-own-dial-up-isp-with-a-raspberry-pi/"
            "pi-isp-ibook-hero.jpeg"
        )
        absolute_url = f"https://www.jeffgeerling.com{relative_url}"
        source_html = (
            "<p>Original paragraph.</p>"
            f'<p><img src="{relative_url}" alt="Relative fixture"></p>'
        )
        self.reader._resolve_images_async = lambda _html: None
        self.reader.show_article(
            replace(self.article, link=article_url),
            ReaderDocument(
                raw_html=source_html,
                cleaned_html=source_html,
            ),
        )
        self.reader._image_replacements[absolute_url] = _ResolvedImage(
            data_url="data:image/jpeg;base64,relative-fixture",
            width=700,
            height=420,
            natural_width=700,
            natural_height=420,
        )

        self.reader.set_translation_result(
            self._translation_result(
                (
                    self._paragraph(
                        0,
                        "Original paragraph.",
                        "原文段落译文。",
                    ),
                ),
                source_format=TranslationSourceFormat.CLEANED_HTML,
            )
        )

        rendered_html = self.reader.content.toHtml()
        self.assertIn(
            "data:image/jpeg;base64,relative-fixture",
            rendered_html,
        )
        self.assertNotIn(relative_url, rendered_html)
        self.assertIn("原文段落译文", self.reader.content.toPlainText())

    def test_relative_and_absolute_image_sources_share_one_download(
        self,
    ) -> None:
        article_url = (
            "https://www.jeffgeerling.com/blog/2026/"
            "build-your-own-dial-up-isp-with-a-raspberry-pi/"
        )
        relative_url = "/blog/2026/article/image.jpeg"
        absolute_url = "https://www.jeffgeerling.com/blog/2026/article/image.jpeg"

        class FinishedSignal:
            def connect(self, callback) -> None:
                self.callback = callback

        class PendingReply:
            def __init__(self) -> None:
                self.finished = FinishedSignal()

        class RecordingNetworkManager:
            def __init__(self) -> None:
                self.requests = []

            def get(self, request):
                self.requests.append(request)
                return PendingReply()

        manager = RecordingNetworkManager()
        self.reader._current_article = replace(
            self.article,
            link=article_url,
        )
        self.reader._network_manager = manager

        self.reader._resolve_images_async(
            f'<img src="{relative_url}"><img src="{absolute_url}">'
        )

        self.assertEqual(
            [
                request.url().toString()
                for request in manager.requests
            ],
            [absolute_url],
        )
        request = manager.requests[0]
        self.assertEqual(
            bytes(request.rawHeader("Referer")).decode("utf-8"),
            article_url,
        )
        self.assertIn(
            "image/",
            bytes(request.rawHeader("Accept")).decode("ascii"),
        )
        self.assertIn(
            "Mozilla/5.0",
            str(request.header(QNetworkRequest.UserAgentHeader)),
        )

    def test_completed_image_can_render_before_slow_batch_finishes(
        self,
    ) -> None:
        class SuccessfulReply:
            def __init__(self, payload: bytes) -> None:
                self.payload = payload
                self.deleted = False

            def error(self):
                return QNetworkReply.NoError

            def readAll(self):
                return self.payload

            def deleteLater(self) -> None:
                self.deleted = True

        image = QImage(32, 18, QImage.Format.Format_RGB32)
        image.fill(0xFF336699)
        encoded = QByteArray()
        buffer = QBuffer(encoded)
        self.assertTrue(buffer.open(QIODevice.WriteOnly))
        self.assertTrue(image.save(buffer, "PNG"))
        buffer.close()

        image_url = "https://example.com/progressive.png"
        render_calls: list[str] = []
        self.reader._current_article = self.article
        self.reader._pending_images = 2
        self.reader._is_resolving_images = True
        self.reader._render_current_view = lambda: render_calls.append(
            "rendered"
        )

        reply = SuccessfulReply(bytes(encoded))
        self.reader._on_image_downloaded(
            reply,
            image_url,
            self.reader._image_generation,
        )

        self.assertTrue(reply.deleted)
        self.assertEqual(self.reader._pending_images, 1)
        self.assertTrue(self.reader._is_resolving_images)
        self.assertTrue(self.reader._image_refresh_timer.isActive())
        resolved = self.reader._image_replacements[image_url]
        self.assertEqual(resolved.data_url, "")
        self.assertTrue(resolved.resource_url.startswith("mercury-image://"))
        self.assertIsNotNone(resolved.image)
        display_html = self.reader._replace_resolved_images(
            f'<img src="{image_url}">',
            {image_url: resolved},
        )
        self.assertIn(resolved.resource_url, display_html)
        self.assertNotIn("base64", display_html)
        self.reader._register_image_resources({image_url: resolved})
        for _ in range(2):
            self.reader.content.setHtml(
                self.reader._wrap_html(display_html)
            )
            cached_image = self.reader.content.document().resource(
                QTextDocument.ImageResource,
                QUrl(resolved.resource_url),
            )
            self.assertIsInstance(cached_image, QImage)
            self.assertFalse(cached_image.isNull())

        self.reader._image_refresh_timer.stop()
        self.reader._render_progressive_images()
        self.assertEqual(render_calls, ["rendered"])

    def test_transient_image_failure_retries_once_then_stops(self) -> None:
        class FailedReply:
            def __init__(self) -> None:
                self.deleted = False

            def error(self):
                return QNetworkReply.ConnectionRefusedError

            def deleteLater(self) -> None:
                self.deleted = True

        class FinishedSignal:
            def connect(self, callback) -> None:
                self.callback = callback

        class PendingReply:
            def __init__(self) -> None:
                self.finished = FinishedSignal()

        class RecordingNetworkManager:
            def __init__(self) -> None:
                self.requests = []

            def get(self, request):
                self.requests.append(request)
                return PendingReply()

        image_url = "https://example.com/transient.png"
        manager = RecordingNetworkManager()
        render_calls: list[str] = []
        self.reader._current_article = self.article
        self.reader._network_manager = manager
        self.reader._pending_images = 1
        self.reader._is_resolving_images = True
        self.reader._render_current_view = lambda: render_calls.append(
            "rendered"
        )

        with patch(
            "mercury.ui.article_reader.QTimer.singleShot"
        ) as single_shot:
            first_reply = FailedReply()
            self.reader._on_image_downloaded(
                first_reply,
                image_url,
                self.reader._image_generation,
            )

            self.assertTrue(first_reply.deleted)
            self.assertEqual(self.reader._pending_images, 1)
            self.assertNotIn(image_url, self.reader._failed_image_urls)
            single_shot.assert_called_once()
            retry_callback = single_shot.call_args.args[1]
            retry_callback()

        self.assertEqual(len(manager.requests), 1)

        second_reply = FailedReply()
        self.reader._on_image_downloaded(
            second_reply,
            image_url,
            self.reader._image_generation,
        )

        self.assertTrue(second_reply.deleted)
        self.assertEqual(self.reader._pending_images, 0)
        self.assertFalse(self.reader._is_resolving_images)
        self.assertIn(image_url, self.reader._failed_image_urls)
        self.assertEqual(render_calls, ["rendered"])

    def test_failed_image_batch_still_rerenders_current_view(self) -> None:
        render_calls: list[str] = []
        self.reader._current_article = self.article
        self.reader._is_resolving_images = True
        self.reader._image_replacements.clear()
        self.reader._render_current_view = lambda: render_calls.append(
            "rendered"
        )

        self.reader._apply_image_replacements()

        self.assertFalse(self.reader._is_resolving_images)
        self.assertEqual(render_calls, ["rendered"])

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
