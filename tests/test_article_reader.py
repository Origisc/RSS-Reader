import os
import sys
import unittest
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtGui import QFont, QTextDocument
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
