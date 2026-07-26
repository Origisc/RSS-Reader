from html import escape

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QTextDocument
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


class ArticleReader(QWidget):
    """右侧文章阅读区域。"""

    read_state_change_requested = Signal(str, bool)
    summary_panel_visibility_requested = Signal(bool)
    translation_panel_visibility_requested = Signal(bool)
    tag_panel_visibility_requested = Signal(bool)

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

        self.title_label = QLabel()
        self.title_label.setObjectName("ReaderPanelTitle")

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
        self.tag_toggle_button.setChecked(True)
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
            self.set_bilingual_visible
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
        self._current_article = article
        self._current_document = document or ReaderDocument.from_article(article)
        self._translation_result = None
        self._bilingual_visible = False
        for button in self.view_buttons.values():
            button.setEnabled(True)
        self.read_state_button.setEnabled(True)
        self._update_bilingual_button()
        self._render_current_view()

    def set_view(self, view: ReaderView) -> None:
        """Switch the representation without changing the selected article."""
        self._current_view = view
        self.view_buttons[view].setChecked(True)

        if self._current_article is not None:
            self._render_current_view()

    def set_reader_style(self, style: ReaderStyle) -> None:
        self._reader_style = style.normalized()

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
    ) -> None:
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
            self._bilingual_visible = True

        self._update_bilingual_button()
        if self._current_article is not None:
            self._render_current_view()

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
    ) -> None:
        self._bilingual_show_text = show_bilingual
        self._bilingual_hide_text = show_original
        self._bilingual_available_tooltip = available_tooltip
        self._bilingual_unavailable_tooltip = unavailable_tooltip
        self._bilingual_status = status
        self._translation_unavailable = translation_unavailable
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
                )}"
                "</div>"
            )

        self._show_bilingual_html("".join(pairs))

    def _show_bilingual_html(self, interleaved_html: str) -> None:
        if self._current_article is None:
            return

        article = self._current_article
        safe_title = escape(article.title)
        safe_source = escape(article.source_title)
        safe_source_label = escape(self._source_label)
        safe_note = escape(self._reader_note)
        body = f"""
            <h1>{safe_title}</h1>
            <p class="byline">{safe_source}</p>
            <div class="reader-card">
                <span>{safe_source_label}</span>
                <strong>{safe_source}</strong>
            </div>
            <div class="reader-article bilingual-article">
                {interleaved_html}
            </div>
            <div class="reader-note">{safe_note}</div>
        """
        self.content.setHtml(self._wrap_html(body))

    @staticmethod
    def _text_to_html(text: str) -> str:
        return escape(text).replace("\n", "<br>")

    @staticmethod
    def _markdown_fragment(markdown: str) -> str:
        document = QTextDocument()
        document.setMarkdown(markdown)
        full_html = document.toHtml()
        lowered = full_html.lower()
        body_start = lowered.find("<body")
        body_open_end = full_html.find(">", body_start)
        body_end = lowered.rfind("</body>")

        if body_start < 0 or body_open_end < 0 or body_end < 0:
            return f"<p>{escape(markdown)}</p>"

        return full_html[body_open_end + 1 : body_end]

    def _show_html(self, content_html: str, fallback_status: str) -> None:
        if self._current_article is None:
            return

        article = self._current_article
        safe_title = escape(article.title)
        safe_source = escape(article.source_title)
        safe_source_label = escape(self._source_label)
        safe_note = escape(self._reader_note)
        fallback_html = ""

        if fallback_status:
            fallback_html = (
                f'<div class="reader-warning">{escape(fallback_status)}</div>'
            )

        body = f"""
            <h1>{safe_title}</h1>
            <p class="byline">{safe_source}</p>
            <div class="reader-card">
                <span>{safe_source_label}</span>
                <strong>{safe_source}</strong>
            </div>
            {fallback_html}
            <div class="reader-article">{content_html}</div>
            <div class="reader-note">{safe_note}</div>
        """
        self.content.setHtml(self._wrap_html(body))
        self._resolve_images_async(content_html)

    def _resolve_markdown_images(self, markdown: str) -> str:
        import re
        import base64
        import requests

        def replace_image(match):
            alt = match.group(1)
            src = match.group(2)
            if not src.startswith('http'):
                return match.group(0)
            
            try:
                response = requests.get(src, timeout=10)
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', 'image/jpeg')
                    encoded = base64.b64encode(response.content).decode('utf-8')
                    return f'![{alt}](data:{content_type};base64,{encoded})'
            except Exception:
                pass
            
            return match.group(0)

        return re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_image, markdown)

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

    def _resolve_images(self, html: str) -> str:
        import re
        import base64
        import requests

        def replace_image(match):
            img_tag = match.group(0)
            src_match = re.search(r'src=["\']([^"\']+)["\']', img_tag)
            if not src_match:
                return img_tag
            
            src = src_match.group(1)
            if not src.startswith('http'):
                return img_tag
            
            try:
                response = requests.get(src, timeout=10)
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', 'image/jpeg')
                    encoded = base64.b64encode(response.content).decode('utf-8')
                    return img_tag.replace(src, f'data:{content_type};base64,{encoded}')
            except Exception:
                pass
            
            return img_tag

        return re.sub(r'<img[^>]+>', replace_image, html)

    def _resolve_images_async(self, html: str) -> None:
        import re

        img_urls = re.findall(r'src=["\']([^"\']+)["\']', html)
        http_urls = [url for url in img_urls if url.startswith('http')]

        if not http_urls:
            return

        self._pending_images = len(http_urls)
        self._resolved_html = html
        self._image_replacements = {}

        for url in http_urls:
            request = QNetworkRequest(QUrl(url))
            reply = self._network_manager.get(request)
            reply.finished.connect(
                lambda r=reply, u=url: self._on_image_downloaded(r, u)
            )

    def _on_image_downloaded(self, reply, url):
        try:
            if reply.error() == 0:
                content = reply.readAll()
                content_type = reply.header(QNetworkRequest.ContentTypeHeader)
                if content_type is None:
                    content_type = 'image/jpeg'

                import base64
                encoded = base64.b64encode(bytes(content)).decode('utf-8')
                self._image_replacements[url] = f'data:{content_type};base64,{encoded}'
        except Exception:
            pass

        reply.deleteLater()

        self._pending_images -= 1
        if self._pending_images == 0:
            self._apply_image_replacements()

    def _apply_image_replacements(self):
        if not hasattr(self, '_resolved_html') or not self._image_replacements:
            return

        resolved_html = self._resolved_html
        for url, data_url in self._image_replacements.items():
            resolved_html = resolved_html.replace(url, data_url)

        article = self._current_article
        if article is None:
            return

        safe_title = escape(article.title)
        safe_source = escape(article.source_title)
        safe_source_label = escape(self._source_label)
        safe_note = escape(self._reader_note)

        body = f"""
            <h1>{safe_title}</h1>
            <p class="byline">{safe_source}</p>
            <div class="reader-card">
                <span>{safe_source_label}</span>
                <strong>{safe_source}</strong>
            </div>
            <div class="reader-article">{resolved_html}</div>
            <div class="reader-note">{safe_note}</div>
        """
        self.content.setHtml(self._wrap_html(body))

    def _wrap_html(self, body: str) -> str:
        return f"""
        <!doctype html>
        <html>
        <head>
            <style>
                body {{
                    background: #082435;
                    color: #d7e3ed;
                    font-family: Georgia, "Times New Roman", serif;
                    font-size: {self._reader_style.font_size}px;
                    line-height: {self._reader_style.line_height};
                    margin: 0;
                    padding: 0;
                }}
                .reader-page {{
                    margin: 0 auto;
                    max-width: {self._reader_style.content_width}px;
                    padding: 32px 40px 72px;
                }}
                h1 {{
                    color: #dbe8f5;
                    font-size: 34px;
                    line-height: 1.18;
                    margin: 0 0 18px;
                }}
                .byline {{
                    color: #cbd8e5;
                    font-style: italic;
                    margin: 0 0 22px;
                }}
                .lede {{
                    color: #afc2d2;
                    font-size: {self._reader_style.font_size}px;
                }}
                .reader-card,
                .reader-note,
                .reader-warning {{
                    background: #102f53;
                    border-left: 3px solid #2487ff;
                    border-radius: 6px;
                    color: #dbe8f5;
                    margin: 20px 0;
                    padding: 14px 18px;
                }}
                .reader-card span {{
                    color: #9db4c8;
                    display: block;
                    font-family: "Segoe UI", Arial, sans-serif;
                    font-size: 13px;
                    margin-bottom: 4px;
                }}
                .reader-note {{
                    background: #0f2a3d;
                    border-left-color: #4e7191;
                    color: #adc3d2;
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
                    margin: 0 0 18px;
                }}
                .bilingual-pair {{
                    border-bottom: 1px solid #29485c;
                    margin: 0 0 24px;
                    padding: 0 0 24px;
                }}
                .bilingual-pair:last-child {{
                    border-bottom: 0;
                }}
                .original-paragraph {{
                    color: #d7e3ed;
                    margin-bottom: 10px;
                }}
                .translation-block {{
                    background: #102f53;
                    border-left: 3px solid #2487ff;
                    border-radius: 5px;
                    color: #f0f6fc;
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
                    height: auto;
                    max-width: 100%;
                }}
                .reader-article table {{
                    border-collapse: collapse;
                    margin: 18px 0;
                    width: 100%;
                }}
                .reader-article th,
                .reader-article td {{
                    border: 1px solid #416074;
                    padding: 8px;
                    text-align: left;
                }}
                .reader-article pre,
                .reader-article code {{
                    background: #0f2a3d;
                    border-radius: 4px;
                    font-family: Consolas, "SFMono-Regular", monospace;
                }}
                .reader-article pre {{
                    overflow-wrap: anywhere;
                    padding: 14px;
                }}
                .reader-article a {{
                    color: #69aefc;
                }}
            </style>
        </head>
        <body><div class="reader-page">{body}</div></body>
        </html>
        """
