import hashlib
import re
from dataclasses import dataclass
from html import escape, unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from PySide6.QtCore import Qt, QTimer, Signal, QUrl
from PySide6.QtGui import QImage, QTextDocument
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from mercury.domain import (
    TranslationResult,
    TranslationSourceFormat,
)
from mercury.models.article import Article
from mercury.ui.bilingual_document import (
    interleave_html_translations,
    translation_card_html,
)
from mercury.ui.reader_document import (
    ReaderContentFormat,
    ReaderDocument,
    ReaderView,
)
from mercury.ui.reader_style import ReaderStyle


_IMAGE_TAG_PATTERN = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_IMAGE_SOURCE_PATTERN = re.compile(
    r"(?P<prefix>\bsrc\s*=\s*)(?P<quote>[\"'])"
    r"(?P<source>.*?)(?P=quote)",
    re.IGNORECASE | re.DOTALL,
)
_IMAGE_SIZE_ATTRIBUTE_PATTERN = re.compile(
    r"\s+(?:width|height)\s*=\s*"
    r"(?:[\"'][^\"']*[\"']|[^\s>]+)",
    re.IGNORECASE,
)
_IMAGE_BLOCK_PATTERNS = tuple(
    re.compile(
        (
            rf"<(?P<tag>{tag})\b(?P<attrs>[^>]*)>"
            rf"(?P<body>(?:(?!<{tag}\b).)*?)"
            r"</(?P=tag)\s*>"
        ),
        re.IGNORECASE | re.DOTALL,
    )
    for tag in ("p", "figure", "div")
)
_IMAGE_CAPTION_BLOCK_PATTERN = re.compile(
    (
        r"<(?P<tag>p|figcaption)\b(?P<attrs>[^>]*)>"
        r"(?P<body>.*?)</(?P=tag)\s*>"
    ),
    re.IGNORECASE | re.DOTALL,
)
_STYLE_ATTRIBUTE_PATTERN = re.compile(
    r"(?P<prefix>\bstyle\s*=\s*)(?P<quote>[\"'])"
    r"(?P<style>.*?)(?P=quote)",
    re.IGNORECASE | re.DOTALL,
)
_MEDIA_DIMENSION_STYLE_PATTERN = re.compile(
    r"(?<![-\w])(?:(?:min|max)-)?(?:width|height)"
    r"\s*:\s*[^;]*(?:;|$)",
    re.IGNORECASE,
)
_NUMERIC_IMAGE_WIDTH_PATTERN = re.compile(
    r"\bwidth\s*=\s*[\"']?(?P<value>\d+)",
    re.IGNORECASE,
)
_NUMERIC_IMAGE_HEIGHT_PATTERN = re.compile(
    r"\bheight\s*=\s*[\"']?(?P<value>\d+)",
    re.IGNORECASE,
)
_VOID_HTML_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
_IMAGE_REFRESH_INTERVAL_MS = 60
_IMAGE_RETRY_DELAY_MS = 250
_IMAGE_RETRY_LIMIT = 1
_IMAGE_REQUEST_TIMEOUT_MS = 15000
_IMAGE_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class _BareImageBlockNormalizer(HTMLParser):
    """Give bare images a block independent from adjacent translations."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._output: list[str] = []
        self._stack: list[tuple[str, bool]] = []

    @property
    def html(self) -> str:
        return "".join(self._output)

    def handle_starttag(self, tag: str, attrs) -> None:
        lowered = tag.lower()
        raw_tag = self.get_starttag_text() or f"<{tag}>"
        if lowered == "img" and not self._inside_media_block():
            self._output.append(
                '<p style="line-height:100%;">'
                f"{raw_tag}"
                "</p>"
            )
            return

        self._output.append(raw_tag)
        if lowered not in _VOID_HTML_TAGS:
            self._stack.append(
                (lowered, self._is_media_block(lowered, attrs))
            )

    def handle_startendtag(self, tag: str, attrs) -> None:
        lowered = tag.lower()
        raw_tag = self.get_starttag_text() or f"<{tag} />"
        if lowered == "img" and not self._inside_media_block():
            self._output.append(
                '<p style="line-height:100%;">'
                f"{raw_tag}"
                "</p>"
            )
            return
        self._output.append(raw_tag)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        self._output.append(f"</{tag}>")
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == lowered:
                del self._stack[index:]
                break

    def handle_data(self, data: str) -> None:
        self._output.append(data)

    def handle_entityref(self, name: str) -> None:
        self._output.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self._output.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        self._output.append(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        self._output.append(f"<!{decl}>")

    def handle_pi(self, data: str) -> None:
        self._output.append(f"<?{data}>")

    def _inside_media_block(self) -> bool:
        return any(is_media_block for _, is_media_block in self._stack)

    @staticmethod
    def _is_media_block(tag: str, attrs) -> bool:
        if tag in {"p", "figure"}:
            return True

        style = next(
            (
                str(value or "")
                for name, value in attrs
                if name.lower() == "style"
            ),
            "",
        )
        return bool(
            re.search(
                r"(?:^|;)\s*line-height\s*:\s*100%\s*(?:;|$)",
                style,
                flags=re.IGNORECASE,
            )
        )


@dataclass(frozen=True, slots=True)
class _ResolvedImage:
    data_url: str
    width: int
    height: int
    natural_width: int | None = None
    natural_height: int | None = None
    resource_url: str = ""
    image: QImage | None = None


class ArticleReader(QWidget):
    """右侧文章阅读区域。"""

    read_state_change_requested = Signal(str, bool)
    summary_panel_visibility_requested = Signal(bool)
    translation_panel_visibility_requested = Signal(bool)
    tag_panel_visibility_requested = Signal(bool)
    bilingual_visibility_change_requested = Signal(str, bool)

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("ReaderPanel")
        self._current_article: Article | None = None
        self._welcome_title = ""
        self._welcome_body = ""
        self._source_label = ""
        self._reader_note = ""
        self._current_document: ReaderDocument | None = None
        self._current_view = ReaderView.RAW
        self._reader_style = ReaderStyle()
        self._color_scheme = "dark"
        self._is_read = False
        self._translation_result: TranslationResult | None = None
        self._bilingual_visible = False
        self._bilingual_show_text = "Bilingual"
        self._bilingual_hide_text = "Original only"
        self._bilingual_available_tooltip = (
            "Switch between original-only and paragraph bilingual reading."
        )
        self._bilingual_unavailable_tooltip = (
            "Generate a translation before opening bilingual reading."
        )
        self._bilingual_status = "Showing paragraph bilingual reading"
        self._translation_unavailable = "Translation unavailable"
        self._translation_translating = "Translating..."
        self._mark_read_text = "Mark read"
        self._mark_unread_text = "Mark unread"
        self._view_labels = {
            ReaderView.RAW: "Original",
            ReaderView.CLEANED_HTML: "Cleaned HTML",
            ReaderView.MARKDOWN: "Markdown",
        }
        self._view_statuses = {
            ReaderView.RAW: "Showing original content",
            ReaderView.CLEANED_HTML: "Showing cleaned HTML",
            ReaderView.MARKDOWN: "Showing cleaned Markdown",
        }
        self._fallback_unavailable = (
            "{view} is unavailable; showing original content."
        )
        self._fallback_error = (
            "Cleaning failed: {error}. Showing original content."
        )
        self._link_only_loading = (
            "This Feed only provides a link. Mercury is loading the "
            "article webpage in the background."
        )
        self._link_only_not_found = (
            "The article body could not be loaded because the webpage "
            "returned 404. It may have been removed or moved."
        )
        self._link_only_failed = (
            "The article body could not be loaded: {error}"
        )
        self._link_only_available = (
            "This Feed only provides a link. The webpage content is "
            "available in Cleaned HTML or Markdown."
        )

        self.title_label = QLabel()
        self.title_label.setObjectName("ReaderPanelTitle")
        self.title_label.hide()

        self.view_toolbar = QFrame()
        self.view_toolbar.setObjectName("ReaderToolbar")
        self.view_button_group = QButtonGroup(self)
        self.view_button_group.setExclusive(True)
        self.view_buttons: dict[ReaderView, QPushButton] = {}

        toolbar_layout = QHBoxLayout(self.view_toolbar)
        toolbar_layout.setContentsMargins(12, 6, 10, 6)
        toolbar_layout.setSpacing(6)
        toolbar_layout.addWidget(self.title_label)
        toolbar_layout.addStretch(1)

        for view in ReaderView:
            button = QPushButton()
            button.setObjectName("ReaderViewButton")
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked, selected_view=view: self._select_view(
                    selected_view,
                    checked,
                )
            )
            self.view_button_group.addButton(button)
            self.view_buttons[view] = button
            toolbar_layout.addWidget(button)

        self.view_buttons[ReaderView.RAW].setChecked(True)

        self.view_status_label = QLabel()
        self.view_status_label.setObjectName("ReaderViewStatus")
        self.view_status_label.setWordWrap(True)
        toolbar_layout.addWidget(self.view_status_label)

        self.tag_toggle_button = QPushButton()
        self.tag_toggle_button.setObjectName("ReaderUtilityButton")
        self.tag_toggle_button.setCheckable(True)
        self.tag_toggle_button.setChecked(False)
        self.tag_toggle_button.clicked.connect(
            lambda checked: self.tag_panel_visibility_requested.emit(checked)
        )
        toolbar_layout.addWidget(self.tag_toggle_button)

        self.summary_toggle_button = QPushButton()
        self.summary_toggle_button.setObjectName("ReaderUtilityButton")
        self.summary_toggle_button.setCheckable(True)
        self.summary_toggle_button.setChecked(True)
        self.summary_toggle_button.clicked.connect(
            lambda checked: self.summary_panel_visibility_requested.emit(
                checked
            )
        )
        toolbar_layout.addWidget(self.summary_toggle_button)

        self.translation_toggle_button = QPushButton()
        self.translation_toggle_button.setObjectName("ReaderUtilityButton")
        self.translation_toggle_button.setCheckable(True)
        self.translation_toggle_button.setChecked(False)
        self.translation_toggle_button.clicked.connect(
            lambda checked: self.translation_panel_visibility_requested.emit(
                checked
            )
        )
        toolbar_layout.addWidget(self.translation_toggle_button)

        self.bilingual_view_button = QPushButton()
        self.bilingual_view_button.setObjectName("ReaderUtilityButton")
        self.bilingual_view_button.setCheckable(True)
        self.bilingual_view_button.clicked.connect(
            self._request_bilingual_visibility_change
        )
        toolbar_layout.addWidget(self.bilingual_view_button)

        self.read_state_button = QPushButton()
        self.read_state_button.setObjectName("ReaderUtilityButton")
        self.read_state_button.clicked.connect(
            self._request_read_state_change
        )
        toolbar_layout.addWidget(self.read_state_button)

        self.content = QTextBrowser()
        self.content.setObjectName("ReaderContent")
        self.content.setOpenExternalLinks(True)
        self._network_manager = QNetworkAccessManager()
        self.content.document().setMetaInformation(QTextDocument.DocumentUrl, "")
        self._image_replacements: dict[str, _ResolvedImage] = {}
        self._failed_image_urls: set[str] = set()
        self._image_retry_counts: dict[str, int] = {}
        self._image_generation = 0
        self._is_resolving_images = False
        self._pending_images = 0
        self._last_image_max_width = 0
        self._image_refresh_timer = QTimer(self)
        self._image_refresh_timer.setSingleShot(True)
        self._image_refresh_timer.setInterval(
            _IMAGE_REFRESH_INTERVAL_MS
        )
        self._image_refresh_timer.timeout.connect(
            self._render_progressive_images
        )
        self._image_resize_timer = QTimer(self)
        self._image_resize_timer.setSingleShot(True)
        self._image_resize_timer.setInterval(80)
        self._image_resize_timer.timeout.connect(
            self._rerender_images_after_resize
        )

        self.reader_body = QFrame()
        self.reader_body.setObjectName("ReaderBody")
        self.reader_body_layout = QGridLayout(self.reader_body)
        self.reader_body_layout.setContentsMargins(0, 0, 0, 0)
        self.reader_body_layout.setSpacing(0)
        self.reader_body_layout.addWidget(self.content, 0, 0)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.view_toolbar)
        self.main_layout.addWidget(self.reader_body, 1)
        self.view_status_label.hide()
        self._update_bilingual_button()

    @property
    def current_view(self) -> ReaderView:
        return self._current_view

    @property
    def current_article_id(self) -> str | None:
        if self._current_article is None:
            return None

        return self._current_article.id

    @property
    def reader_style(self) -> ReaderStyle:
        return self._reader_style

    @property
    def bilingual_visible(self) -> bool:
        return self._bilingual_visible

    @property
    def translation_result(self) -> TranslationResult | None:
        return self._translation_result

    def show_welcome(self) -> None:
        self._reset_image_context()
        self._current_article = None
        self._current_document = None
        self._is_read = False
        self._translation_result = None
        self._bilingual_visible = False
        for button in self.view_buttons.values():
            button.setEnabled(False)
        self.read_state_button.setEnabled(False)
        self._update_bilingual_button()
        self.view_status_label.clear()
        self.view_status_label.hide()
        body = (
            f"<h1>{escape(self._welcome_title)}</h1>"
            f"<p class='lede'>{escape(self._welcome_body)}</p>"
        )
        self.content.setHtml(self._wrap_html(body))

    def show_article(
        self,
        article: Article,
        document: ReaderDocument | None = None,
    ) -> None:
        if self.current_article_id != article.id:
            self._reset_image_context()
        self._current_article = article
        self._current_document = document or ReaderDocument.from_article(article)
        self._translation_result = None
        self._bilingual_visible = False
        for button in self.view_buttons.values():
            button.setEnabled(True)
        self.read_state_button.setEnabled(True)
        self._update_bilingual_button()
        self._render_current_view()

    def _reset_image_context(self) -> None:
        self._image_generation += 1
        self._image_replacements.clear()
        self._failed_image_urls.clear()
        self._image_retry_counts.clear()
        self._is_resolving_images = False
        self._pending_images = 0
        self._last_image_max_width = 0
        self._image_refresh_timer.stop()
        self._image_resize_timer.stop()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._current_article is not None and self._image_replacements:
            self._image_resize_timer.start()

    def _rerender_images_after_resize(self) -> None:
        if self._current_article is None or not self._image_replacements:
            return
        if self._image_max_width() == self._last_image_max_width:
            return

        self._render_current_view()

    def set_view(self, view: ReaderView) -> None:
        """Switch the representation without changing the selected article."""
        self._current_view = view
        self.view_buttons[view].setChecked(True)

        if self._current_article is not None:
            self._render_current_view()

    def set_content_issue_texts(
        self,
        *,
        link_only_loading: str,
        link_only_not_found: str,
        link_only_failed: str,
        link_only_available: str,
    ) -> None:
        self._link_only_loading = link_only_loading
        self._link_only_not_found = link_only_not_found
        self._link_only_failed = link_only_failed
        self._link_only_available = link_only_available

        if self._current_article is not None:
            self._render_current_view()

    def set_reader_style(self, style: ReaderStyle) -> None:
        self._reader_style = style.normalized()

        if self._current_article is None:
            self.show_welcome()
            return

        self._render_current_view()

    def set_color_scheme(self, theme: str) -> None:
        self._color_scheme = "light" if theme == "light" else "dark"

        if self._current_article is None:
            self.show_welcome()
            return

        self._render_current_view()

    def set_read_state(self, is_read: bool) -> None:
        self._is_read = is_read
        self._update_read_state_button()

    def set_summary_panel_visible(self, is_visible: bool) -> None:
        self.summary_toggle_button.setChecked(is_visible)

    def set_translation_panel_visible(self, is_visible: bool) -> None:
        self.translation_toggle_button.setChecked(is_visible)

    def set_translation_controls_widget(self, widget: QWidget) -> None:
        """Place translation controls above the article, not below it."""
        self.main_layout.insertWidget(1, widget)

    def set_translation_result(
        self,
        result: TranslationResult | None,
        *,
        visible: bool | None = None,
    ) -> None:
        previous_result = self._translation_result
        previous_visible = self._bilingual_visible
        if (
            result is None
            or self._current_article is None
            or result.article_id != self._current_article.id
            or not result.paragraphs
        ):
            self._translation_result = None
            self._bilingual_visible = False
        else:
            self._translation_result = result
            same_result_article = (
                previous_result is not None
                and previous_result.article_id == result.article_id
            )
            if visible is not None:
                self._bilingual_visible = bool(visible)
            elif same_result_article:
                self._bilingual_visible = previous_visible
            else:
                self._bilingual_visible = True

        self._update_bilingual_button()
        if self._current_article is not None:
            self._render_current_view()

    def _request_bilingual_visibility_change(self, visible: bool) -> None:
        self.set_bilingual_visible(visible)
        if self._current_article is not None:
            self.bilingual_visibility_change_requested.emit(
                self._current_article.id,
                self._bilingual_visible,
            )

    def set_bilingual_visible(self, visible: bool) -> None:
        can_show = (
            self._current_article is not None
            and self._translation_result is not None
            and self._translation_result.article_id
            == self._current_article.id
            and bool(self._translation_result.paragraphs)
        )
        self._bilingual_visible = bool(visible and can_show)
        self._update_bilingual_button()

        if self._current_article is not None:
            self._render_current_view()

    def set_tag_panel_visible(self, is_visible: bool) -> None:
        self.tag_toggle_button.setChecked(is_visible)

    def set_overlay_widget(self, widget: QWidget) -> None:
        self.reader_body_layout.addWidget(
            widget,
            0,
            0,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )

    def set_tag_toggle_texts(self, text: str, tooltip: str) -> None:
        self.tag_toggle_button.setText(text)
        self.tag_toggle_button.setToolTip(tooltip)

    def set_summary_toggle_texts(self, text: str, tooltip: str) -> None:
        self.summary_toggle_button.setText(text)
        self.summary_toggle_button.setToolTip(tooltip)

    def set_translation_toggle_texts(
        self,
        text: str,
        tooltip: str,
    ) -> None:
        self.translation_toggle_button.setText(text)
        self.translation_toggle_button.setToolTip(tooltip)

    def set_translation_view_texts(
        self,
        *,
        show_bilingual: str,
        show_original: str,
        available_tooltip: str,
        unavailable_tooltip: str,
        status: str,
        translation_unavailable: str,
        translation_translating: str,
    ) -> None:
        self._bilingual_show_text = show_bilingual
        self._bilingual_hide_text = show_original
        self._bilingual_available_tooltip = available_tooltip
        self._bilingual_unavailable_tooltip = unavailable_tooltip
        self._bilingual_status = status
        self._translation_unavailable = translation_unavailable
        self._translation_translating = translation_translating
        self._update_bilingual_button()

        if self._bilingual_visible:
            self._render_current_view()

    def set_read_state_texts(
        self,
        *,
        mark_read: str,
        mark_unread: str,
    ) -> None:
        self._mark_read_text = mark_read
        self._mark_unread_text = mark_unread
        self._update_read_state_button()

    def set_view_texts(
        self,
        *,
        raw_label: str,
        cleaned_html_label: str,
        markdown_label: str,
        raw_status: str,
        cleaned_html_status: str,
        markdown_status: str,
        fallback_unavailable: str,
        fallback_error: str,
    ) -> None:
        self._view_labels = {
            ReaderView.RAW: raw_label,
            ReaderView.CLEANED_HTML: cleaned_html_label,
            ReaderView.MARKDOWN: markdown_label,
        }
        self._view_statuses = {
            ReaderView.RAW: raw_status,
            ReaderView.CLEANED_HTML: cleaned_html_status,
            ReaderView.MARKDOWN: markdown_status,
        }
        self._fallback_unavailable = fallback_unavailable
        self._fallback_error = fallback_error

        for view, button in self.view_buttons.items():
            button.setText(self._view_labels[view])

        if self._current_article is not None:
            self._render_current_view()

    def _select_view(self, view: ReaderView, checked: bool) -> None:
        if checked:
            self.set_view(view)

    def _request_read_state_change(self) -> None:
        if self._current_article is None:
            return

        self.read_state_change_requested.emit(
            self._current_article.id,
            not self._is_read,
        )

    def _update_read_state_button(self) -> None:
        if self._is_read:
            self.read_state_button.setText(self._mark_unread_text)
            return

        self.read_state_button.setText(self._mark_read_text)

    def _update_bilingual_button(self) -> None:
        has_result = (
            self._current_article is not None
            and self._translation_result is not None
            and self._translation_result.article_id
            == self._current_article.id
            and bool(self._translation_result.paragraphs)
        )
        self.bilingual_view_button.setEnabled(has_result)
        self.bilingual_view_button.setChecked(
            has_result and self._bilingual_visible
        )
        self.bilingual_view_button.setText(
            self._bilingual_hide_text
            if has_result and self._bilingual_visible
            else self._bilingual_show_text
        )
        self.bilingual_view_button.setToolTip(
            self._bilingual_available_tooltip
            if has_result
            else self._bilingual_unavailable_tooltip
        )

    def _render_current_view(self) -> None:
        if self._current_article is None or self._current_document is None:
            return

        if (
            self._bilingual_visible
            and self._translation_result is not None
            and self._translation_result.article_id
            == self._current_article.id
        ):
            for button in self.view_buttons.values():
                button.setEnabled(False)
            self.view_status_label.setText(self._bilingual_status)
            self.view_status_label.hide()
            self._show_bilingual_result(self._translation_result)
            return

        for button in self.view_buttons.values():
            button.setEnabled(True)
        rendered = self._current_document.resolve(self._current_view)
        status = self._view_statuses[self._current_view]

        if rendered.used_fallback:
            if self._current_document.cleaning_error:
                status = self._fallback_error.format(
                    error=self._current_document.cleaning_error,
                )
            else:
                status = self._fallback_unavailable.format(
                    view=self._view_labels[self._current_view],
                )

        self.view_status_label.setText(status)
        self.view_status_label.setVisible(rendered.used_fallback)

        if rendered.content_format is ReaderContentFormat.MARKDOWN:
            self._show_markdown(rendered.content)
            return

        self._show_html(rendered.content, status if rendered.used_fallback else "")

    def _show_bilingual_result(self, result: TranslationResult) -> None:
        if self._current_article is None or self._current_document is None:
            return

        if result.source_format is not TranslationSourceFormat.CLEANED_MARKDOWN:
            source_html = (
                self._current_document.cleaned_html
                if result.source_format is TranslationSourceFormat.CLEANED_HTML
                else self._current_document.raw_html
            )
            if source_html:
                interleaved = interleave_html_translations(
                    source_html,
                    result.paragraphs,
                    self._translation_unavailable,
                    self._translation_translating,
                )
                if interleaved.fully_aligned:
                    self._show_bilingual_html(interleaved.html)
                    return

        pairs: list[str] = []
        for paragraph in result.paragraphs:
            if result.source_format is TranslationSourceFormat.CLEANED_MARKDOWN:
                original_html = self._markdown_fragment(
                    paragraph.original_text
                )
            else:
                original_html = (
                    f"<p>{self._text_to_html(paragraph.original_text)}</p>"
                )

            pairs.append(
                '<div class="bilingual-pair">'
                f'<div class="original-paragraph">{original_html}</div>'
                f"{translation_card_html(
                    paragraph,
                    self._translation_unavailable,
                    self._translation_translating,
                )}"
                "</div>"
            )

        self._show_bilingual_html("".join(pairs))

    def _show_bilingual_html(self, interleaved_html: str) -> None:
        if self._current_article is None:
            return

        scroll_pos = self.content.verticalScrollBar().value()
        article = self._current_article
        normalized_html = self._normalize_image_paragraphs(
            ReaderDocument.prepare_for_embedding(interleaved_html)
        )
        image_replacements = self._scaled_image_replacements()
        display_html = self._replace_resolved_images(
            normalized_html,
            image_replacements,
            base_url=article.link,
        )

        safe_title = escape(article.title)
        safe_source = escape(article.source_title)
        body = f"""
            <h1>{safe_title}</h1>
            <p class="byline">{safe_source}</p>
            <div class="reader-article bilingual-article">
                {display_html}
            </div>
        """
        self._set_document_base_url(article.link)
        self._register_image_resources(image_replacements)
        self.content.setHtml(self._wrap_html(body))
        self.content.verticalScrollBar().setValue(scroll_pos)
        self._resolve_images_async(normalized_html)

    @staticmethod
    def _text_to_html(text: str) -> str:
        return escape(text).replace("\n", "<br>")

    @staticmethod
    def _markdown_fragment(markdown: str) -> str:
        from mercury.services.markdown_converter import MarkdownRenderer
        renderer = MarkdownRenderer()
        return renderer.render(markdown)

    def _show_html(self, content_html: str, fallback_status: str) -> None:
        if self._current_article is None:
            return

        scroll_pos = self.content.verticalScrollBar().value()
        article = self._current_article
        normalized_content_html = self._normalize_image_paragraphs(
            ReaderDocument.prepare_for_embedding(content_html)
        )
        image_replacements = self._scaled_image_replacements()
        display_content_html = self._replace_resolved_images(
            normalized_content_html,
            image_replacements,
            base_url=article.link,
        )

        safe_title = escape(article.title)
        safe_source = escape(article.source_title)
        fallback_html = ""
        issue_html = ""

        if fallback_status:
            fallback_html = (
                f'<div class="reader-warning">{escape(fallback_status)}</div>'
            )
        content_issue = self._content_issue_message(content_html)
        if content_issue:
            issue_html = (
                f'<div class="reader-warning">{escape(content_issue)}</div>'
            )

        body = f"""
            <h1>{safe_title}</h1>
            <p class="byline">{safe_source}</p>
            {fallback_html}
            {issue_html}
            <div class="reader-article">{display_content_html}</div>
        """
        self._set_document_base_url(article.link)
        self._register_image_resources(image_replacements)
        self.content.setHtml(self._wrap_html(body))
        self.content.verticalScrollBar().setValue(scroll_pos)
        self._resolve_images_async(normalized_content_html)

    def _content_issue_message(self, content_html: str) -> str:
        article = self._current_article
        if article is None or not self._is_link_only_content(content_html):
            return ""

        if (
            article.original_html
            or article.cleaned_html
            or article.cleaned_markdown
        ):
            if self._current_view is ReaderView.RAW:
                return self._link_only_available
            return ""

        if article.fetch_status == "failed":
            error = str(article.fetch_error or "").strip()
            if re.search(r"\b404\b|not[\s_-]*found", error, re.IGNORECASE):
                return self._link_only_not_found
            return self._link_only_failed.format(
                error=error or "Unknown fetch error",
            )

        return self._link_only_loading

    @staticmethod
    def _is_link_only_content(content_html: str) -> bool:
        anchors = re.findall(
            r"<a\b[^>]*>(.*?)</a\s*>",
            content_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not anchors:
            return False

        outside_anchors = re.sub(
            r"<a\b[^>]*>.*?</a\s*>",
            "",
            content_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        outside_text = re.sub(r"<[^>]+>", " ", outside_anchors)
        if re.sub(r"\s+", "", unescape(outside_text)):
            return False

        for anchor_body in anchors:
            anchor_text = unescape(
                re.sub(r"<[^>]+>", "", anchor_body)
            ).strip()
            if not re.match(r"^https?://\S+$", anchor_text, re.IGNORECASE):
                return False

        return True

    def _show_markdown(self, markdown: str) -> None:
        if self._current_article is None:
            return

        markdown_html = self._markdown_fragment(markdown)
        self._show_html(markdown_html, "")

    def set_texts(
        self,
        title: str,
        welcome_title: str,
        welcome_body: str,
        source_label: str,
        reader_note: str,
    ) -> None:
        self.title_label.setText(title)
        self._welcome_title = welcome_title
        self._welcome_body = welcome_body
        self._source_label = source_label
        self._reader_note = reader_note

        if self._current_article is None:
            self.show_welcome()
            return

        self._render_current_view()

    def _resolve_images_async(self, html: str) -> None:
        if self._is_resolving_images:
            return

        img_urls = re.findall(r'src=["\']([^"\']+)["\']', html)
        http_urls = [
            url
            for url in dict.fromkeys(
                self._canonical_image_url(source)
                for source in img_urls
            )
            if urlparse(url).scheme in {"http", "https"}
            and url not in self._image_replacements
            and url not in self._failed_image_urls
        ]

        if not http_urls:
            return

        self._is_resolving_images = True
        self._pending_images = len(http_urls)
        generation = self._image_generation

        for url in http_urls:
            self._request_image(url, generation)

    def _request_image(self, url: str, generation: int) -> None:
        if generation != self._image_generation:
            return

        request = QNetworkRequest(QUrl(url))
        request.setTransferTimeout(_IMAGE_REQUEST_TIMEOUT_MS)
        request.setHeader(
            QNetworkRequest.UserAgentHeader,
            _IMAGE_USER_AGENT,
        )
        request.setRawHeader(
            b"Accept",
            (
                b"image/png,image/jpeg,image/webp,image/gif,"
                b"image/svg+xml,image/*;q=0.8,*/*;q=0.5"
            ),
        )
        article = self._current_article
        if article is not None and article.link:
            request.setRawHeader(
                b"Referer",
                QUrl(article.link).toEncoded(),
            )

        reply = self._network_manager.get(request)
        reply.finished.connect(
            lambda r=reply, u=url, g=generation: (
                self._on_image_downloaded(r, u, g)
            )
        )

    def _retry_image(self, url: str, generation: int) -> None:
        if (
            generation != self._image_generation
            or not self._is_resolving_images
        ):
            return
        self._request_image(url, generation)

    def _on_image_downloaded(self, reply, url, generation: int):
        from PySide6.QtNetwork import QNetworkReply

        if generation != self._image_generation:
            reply.deleteLater()
            return

        resolved = False
        try:
            error = reply.error()

            if error == QNetworkReply.NoError:
                content = reply.readAll()
                image_bytes = bytes(content)
                image = QImage.fromData(image_bytes)

                if not image.isNull():
                    width, height = self._scaled_image_size(
                        image.width(),
                        image.height(),
                    )
                    resource_url = self._image_resource_url(url)
                    self._image_replacements[url] = _ResolvedImage(
                        data_url="",
                        width=width,
                        height=height,
                        natural_width=image.width(),
                        natural_height=image.height(),
                        resource_url=resource_url,
                        image=image,
                    )
                    resolved = True
        except Exception:
            # A failed image must never make the cached article unreadable.
            pass

        reply.deleteLater()

        if resolved:
            self._image_retry_counts.pop(url, None)
            self._image_refresh_timer.start()
        else:
            retry_count = self._image_retry_counts.get(url, 0)
            if retry_count < _IMAGE_RETRY_LIMIT:
                self._image_retry_counts[url] = retry_count + 1
                QTimer.singleShot(
                    _IMAGE_RETRY_DELAY_MS,
                    lambda u=url, g=generation: self._retry_image(u, g),
                )
                return
            self._failed_image_urls.add(url)

        self._pending_images -= 1
        if self._pending_images == 0:
            self._is_resolving_images = False
            if not self._image_refresh_timer.isActive():
                self._apply_image_replacements()

    def _scaled_image_size(
        self,
        source_width: int,
        source_height: int,
    ) -> tuple[int, int]:
        max_width = self._image_max_width()
        if source_width <= 0 or source_height <= 0:
            return 1, 1

        scale = min(1.0, max_width / source_width)
        return (
            max(1, round(source_width * scale)),
            max(1, round(source_height * scale)),
        )

    def _image_max_width(self) -> int:
        configured_width = self._reader_style.normalized().content_width
        if not self.isVisible():
            return configured_width

        viewport_width = self.content.viewport().width()
        page_padding = 108
        visible_width = max(120, viewport_width - page_padding)
        return min(configured_width, visible_width)

    def _scaled_image_replacements(self) -> dict[str, _ResolvedImage]:
        scaled: dict[str, _ResolvedImage] = {}
        for url, image in self._image_replacements.items():
            natural_width = image.natural_width or image.width
            natural_height = image.natural_height or image.height
            width, height = self._scaled_image_size(
                natural_width,
                natural_height,
            )
            scaled[url] = _ResolvedImage(
                data_url=image.data_url,
                width=width,
                height=height,
                natural_width=natural_width,
                natural_height=natural_height,
                resource_url=image.resource_url,
                image=image.image,
            )

        if scaled:
            self._last_image_max_width = self._image_max_width()
        return scaled

    def _replace_resolved_images(
        self,
        html: str,
        replacements: dict[str, _ResolvedImage],
        *,
        base_url: str = "",
    ) -> str:
        def replace_tag(match: re.Match[str]) -> str:
            tag = match.group(0)
            source_match = _IMAGE_SOURCE_PATTERN.search(tag)
            if source_match is None:
                return tag

            source = unescape(source_match.group("source")).strip()
            replacement = replacements.get(source)
            if replacement is None and base_url:
                replacement = replacements.get(urljoin(base_url, source))
            if replacement is None:
                return self._fit_declared_image_size(tag)

            tag = _IMAGE_SIZE_ATTRIBUTE_PATTERN.sub("", tag)
            display_source = (
                replacement.resource_url or replacement.data_url
            )
            tag = _IMAGE_SOURCE_PATTERN.sub(
                lambda source: (
                    f'{source.group("prefix")}{source.group("quote")}'
                    f'{display_source}{source.group("quote")}'
                ),
                tag,
                count=1,
            )
            size_attributes = (
                f' width="{replacement.width}"'
                f' height="{replacement.height}"'
            )
            if tag.endswith("/>"):
                return f"{tag[:-2].rstrip()}{size_attributes} />"
            return f"{tag[:-1].rstrip()}{size_attributes}>"

        resolved_html = _IMAGE_TAG_PATTERN.sub(replace_tag, html)
        return self._normalize_image_paragraphs(resolved_html)

    def _fit_declared_image_size(self, tag: str) -> str:
        """Keep pending remote images inside the current Reader viewport."""
        width_match = _NUMERIC_IMAGE_WIDTH_PATTERN.search(tag)
        height_match = _NUMERIC_IMAGE_HEIGHT_PATTERN.search(tag)
        if width_match is None or height_match is None:
            return tag

        source_width = int(width_match.group("value"))
        source_height = int(height_match.group("value"))
        width, height = self._scaled_image_size(
            source_width,
            source_height,
        )
        if (width, height) == (source_width, source_height):
            return tag

        tag = _IMAGE_SIZE_ATTRIBUTE_PATTERN.sub("", tag)
        size_attributes = f' width="{width}" height="{height}"'
        if tag.endswith("/>"):
            return f"{tag[:-2].rstrip()}{size_attributes} />"
        return f"{tag[:-1].rstrip()}{size_attributes}>"

    @staticmethod
    def _image_resource_url(source_url: str) -> str:
        digest = hashlib.sha256(
            source_url.encode("utf-8")
        ).hexdigest()
        return f"mercury-image://cache/{digest}"

    def _register_image_resources(
        self,
        replacements: dict[str, _ResolvedImage],
    ) -> None:
        for resolved in replacements.values():
            if (
                not resolved.resource_url
                or resolved.image is None
                or resolved.image.isNull()
            ):
                continue
            self.content.document().addResource(
                QTextDocument.ImageResource,
                QUrl(resolved.resource_url),
                resolved.image,
            )

    def _canonical_image_url(self, source: str) -> str:
        source = unescape(source).strip()
        if not source:
            return ""

        article_url = (
            self._current_article.link
            if self._current_article is not None
            else ""
        )
        return urljoin(article_url, source)

    def _set_document_base_url(self, article_url: str) -> None:
        if article_url:
            self.content.document().setBaseUrl(QUrl(article_url))
        else:
            self.content.document().setBaseUrl(QUrl())

    @staticmethod
    def _normalize_image_paragraphs(html: str) -> str:
        """Keep proportional article line height from scaling image blocks."""

        def normalize_block(match: re.Match[str]) -> str:
            body = match.group("body")
            if _IMAGE_TAG_PATTERN.search(body) is None:
                return match.group(0)

            attrs = ArticleReader._set_inline_line_height(
                ArticleReader._strip_media_container_dimensions(
                    match.group("attrs")
                ),
                "100%",
            )
            visible_text = unescape(
                re.sub(r"<[^>]+>", "", body)
            ).strip()

            if visible_text:
                body = _IMAGE_CAPTION_BLOCK_PATTERN.sub(
                    lambda caption: (
                        f'<{caption.group("tag")}'
                        f'{ArticleReader._set_inline_line_height(
                            caption.group("attrs"),
                            "normal",
                        )}>'
                        f'{caption.group("body")}'
                        f'</{caption.group("tag")}>'
                    ),
                    body,
                )

                # WordPress commonly wraps an image and its caption in one
                # ``div``. QTextDocument applies the article's proportional
                # line height to the image-owning div, reserving a second
                # fraction of the image below it. Keep the media block at
                # 100%, while caption paragraphs return to normal line height.
                return f"<div{attrs}>{body}</div>"

            # QTextDocument ignores ``figure`` styling and applies the
            # article line-height to the image itself. A presentation-only
            # paragraph keeps the semantic source unchanged in storage while
            # giving Qt a block whose line height it can size correctly.
            return f"<p{attrs}>{body}</p>"

        normalized = html
        for block_pattern in _IMAGE_BLOCK_PATTERNS:
            normalized = block_pattern.sub(normalize_block, normalized)

        # Some cleaned articles place ``img`` directly between paragraphs.
        # After translation cards are interleaved, QTextDocument otherwise
        # merges that inline image into the preceding translation block. The
        # inherited proportional line height then reserves a large empty area
        # below the image and can carry the translation background beside it.
        bare_image_normalizer = _BareImageBlockNormalizer()
        try:
            bare_image_normalizer.feed(normalized)
            bare_image_normalizer.close()
        except Exception:
            return normalized
        return bare_image_normalizer.html

    @staticmethod
    def _strip_media_container_dimensions(attrs: str) -> str:
        """Remove source-site fixed sizing from image-owning wrappers.

        WordPress captions commonly use a wrapper such as
        ``style="width: 760px"``. QTextDocument treats that as a hard minimum
        even after the image itself is scaled, which clips the Reader on a
        narrow window. The downloaded image receives explicit proportional
        dimensions separately, so wrapper dimensions are presentation-only.
        """
        attrs = _IMAGE_SIZE_ATTRIBUTE_PATTERN.sub("", attrs)

        def clean_style(match: re.Match[str]) -> str:
            style = _MEDIA_DIMENSION_STYLE_PATTERN.sub(
                "",
                match.group("style"),
            )
            style = re.sub(r";{2,}", ";", style).strip(" ;")
            if not style:
                return ""
            quote = match.group("quote")
            return (
                f"{match.group('prefix')}{quote}"
                f"{style};{quote}"
            )

        return _STYLE_ATTRIBUTE_PATTERN.sub(clean_style, attrs)

    @staticmethod
    def _set_inline_line_height(attrs: str, value: str) -> str:
        style_match = _STYLE_ATTRIBUTE_PATTERN.search(attrs)
        if style_match is None:
            return f'{attrs} style="line-height:{value};"'

        style = re.sub(
            r"\s*line-height\s*:\s*[^;]+;?",
            "",
            style_match.group("style"),
            flags=re.IGNORECASE,
        )
        replacement = (
            f'{style_match.group("prefix")}'
            f'{style_match.group("quote")}'
            f'line-height:{value};{style}'
            f'{style_match.group("quote")}'
        )
        return (
            f"{attrs[:style_match.start()]}"
            f"{replacement}"
            f"{attrs[style_match.end():]}"
        )

    def _render_progressive_images(self) -> None:
        if self._current_article is not None:
            self._render_current_view()

    def _apply_image_replacements(self) -> None:
        self._image_refresh_timer.stop()
        self._is_resolving_images = False
        if self._current_article is not None:
            self._render_current_view()

    def _wrap_html(self, body: str) -> str:
        paragraph_spacing = self._reader_style.paragraph_spacing_px
        if self._color_scheme == "light":
            palette = {
                "background": "#ffffff",
                "text": "#202124",
                "title": "#17181a",
                "muted": "#6f7378",
                "surface": "#f3f5f7",
                "surface_text": "#25313c",
                "border": "#d7dce1",
                "code": "#f0f2f4",
                "link": "#0a66cc",
                "translation": "#eaf3ff",
            }
        else:
            palette = {
                "background": "#191b1f",
                "text": "#e8e3da",
                "title": "#f7f3ec",
                "muted": "#aaa49b",
                "surface": "#24272c",
                "surface_text": "#edf0f3",
                "border": "#3a3f46",
                "code": "#24272c",
                "link": "#73adff",
                "translation": "#23354a",
            }
        return f"""
        <!doctype html>
        <html>
        <head>
            <style>
                body {{
                    background: {palette["background"]};
                    color: {palette["text"]};
                    font-family: Georgia, "Times New Roman", serif;
                    font-size: {self._reader_style.font_size}px;
                    line-height: {self._reader_style.line_height};
                    margin: 0;
                    padding: 0;
                }}
                .reader-page {{
                    margin: 0 auto;
                    max-width: {self._reader_style.content_width}px;
                    padding: 46px 54px 76px;
                }}
                h1 {{
                    color: {palette["title"]};
                    font-size: 38px;
                    line-height: 1.18;
                    margin: 0 0 14px;
                }}
                .byline {{
                    color: {palette["muted"]};
                    font-style: italic;
                    margin: 0 0 30px;
                }}
                .lede {{
                    color: {palette["muted"]};
                    font-size: {self._reader_style.font_size}px;
                }}
                .reader-card,
                .reader-note,
                .reader-warning {{
                    background: {palette["surface"]};
                    border-left: 3px solid #2487ff;
                    border-radius: 6px;
                    color: {palette["surface_text"]};
                    margin: 20px 0;
                    padding: 14px 18px;
                }}
                .reader-card span {{
                    color: {palette["muted"]};
                    display: block;
                    font-family: "Segoe UI", Arial, sans-serif;
                    font-size: 13px;
                    margin-bottom: 4px;
                }}
                .reader-note {{
                    background: {palette["surface"]};
                    border-left-color: {palette["border"]};
                    color: {palette["muted"]};
                    font-family: "Segoe UI", Arial, sans-serif;
                    font-size: 13px;
                }}
                .reader-warning {{
                    background: #493513;
                    border-left-color: #e6a23c;
                    color: #ffe2a8;
                    font-family: "Segoe UI", Arial, sans-serif;
                    font-size: 13px;
                }}
                .reader-article p {{
                    margin: 0 0 {paragraph_spacing}px;
                }}
                .bilingual-pair {{
                    border-bottom: 1px solid {palette["border"]};
                    margin: 0 0 24px;
                    padding: 0 0 24px;
                }}
                .bilingual-pair:last-child {{
                    border-bottom: 0;
                }}
                .original-paragraph {{
                    color: {palette["text"]};
                    margin-bottom: 10px;
                }}
                .bilingual-article p {{
                    margin: 0;
                }}
                .translation-block {{
                    background: {palette["translation"]};
                    border-left: 3px solid #2487ff;
                    border-radius: 5px;
                    color: {palette["surface_text"]};
                    margin: 8px 0 22px;
                    padding: 12px 16px;
                }}
                .translation-block p {{
                    margin: 0;
                }}
                .translation-table-row td {{
                    border: 0;
                    padding: 0;
                }}
                .translation-partial {{
                    border-left-color: #e6a23c;
                }}
                .translation-unavailable {{
                    background: #2d3035;
                    border-left-color: #718096;
                    color: #b8c4ce;
                    font-style: italic;
                }}
                .reader-article img {{
                    margin: 0;
                    vertical-align: top;
                }}
                .reader-article figure {{
                    line-height: 100%;
                    margin: 16px 0;
                    padding: 0;
                }}
                .reader-article table {{
                    border-collapse: collapse;
                    margin: 18px 0;
                    width: 100%;
                }}
                .reader-article th,
                .reader-article td {{
                    border: 1px solid {palette["border"]};
                    padding: 8px;
                    text-align: left;
                }}
                .reader-article pre,
                .reader-article code {{
                    background: {palette["code"]};
                    border-radius: 4px;
                    font-family: Consolas, "SFMono-Regular", monospace;
                }}
                .reader-article pre {{
                    overflow-wrap: anywhere;
                    padding: 14px;
                }}
                .reader-article a {{
                    color: {palette["link"]};
                    word-break: break-all;
                }}
                .reader-article ul,
                .reader-article ol {{
                    margin: 0 0 {paragraph_spacing}px;
                    padding-left: 2em;
                }}
                .reader-article li {{
                    margin: 0.3em 0;
                }}
                .reader-article li > ul,
                .reader-article li > ol {{
                    margin: 0.3em 0;
                }}
                .reader-article h1,
                .reader-article h2,
                .reader-article h3,
                .reader-article h4,
                .reader-article h5,
                .reader-article h6 {{
                    color: {palette["title"]};
                    line-height: 1.3;
                    margin: 1em 0 0.5em;
                }}
                .reader-article h1 {{ font-size: 28px; }}
                .reader-article h2 {{ font-size: 24px; }}
                .reader-article h3 {{ font-size: 20px; }}
                .reader-article h4 {{ font-size: 18px; }}
                .reader-article h5 {{ font-size: 16px; }}
                .reader-article h6 {{ font-size: 14px; }}
                .reader-article blockquote {{
                    border-left: 3px solid {palette["border"]};
                    color: {palette["muted"]};
                    margin: {paragraph_spacing}px 0;
                    padding: 8px 16px;
                }}
                .reader-article hr {{
                    border: none;
                    border-top: 1px solid {palette["border"]};
                    margin: {paragraph_spacing}px 0;
                }}
            </style>
        </head>
        <body><div class="reader-page">{body}</div></body>
        </html>
        """
