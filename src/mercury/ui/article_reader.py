from html import escape

from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from mercury.models.article import Article
from mercury.ui.reader_document import (
    ReaderContentFormat,
    ReaderDocument,
    ReaderView,
)


class ArticleReader(QWidget):
    """右侧文章阅读区域。"""

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
        toolbar_layout.setContentsMargins(12, 6, 12, 6)
        toolbar_layout.setSpacing(6)

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
        toolbar_layout.addStretch(1)

        self.view_status_label = QLabel()
        self.view_status_label.setObjectName("ReaderViewStatus")
        self.view_status_label.setWordWrap(True)
        toolbar_layout.addWidget(self.view_status_label)

        self.content = QTextBrowser()
        self.content.setObjectName("ReaderContent")
        self.content.setOpenExternalLinks(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.title_label)
        layout.addWidget(self.view_toolbar)
        layout.addWidget(self.content)

        self.view_toolbar.hide()

    @property
    def current_view(self) -> ReaderView:
        return self._current_view

    @property
    def current_article_id(self) -> str | None:
        if self._current_article is None:
            return None

        return self._current_article.id

    def show_welcome(self) -> None:
        self._current_article = None
        self._current_document = None
        self.view_toolbar.hide()
        self.view_status_label.clear()
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
        self.view_toolbar.show()
        self._render_current_view()

    def set_view(self, view: ReaderView) -> None:
        """Switch the representation without changing the selected article."""
        self._current_view = view
        self.view_buttons[view].setChecked(True)

        if self._current_article is not None:
            self._render_current_view()

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

    def _render_current_view(self) -> None:
        if self._current_article is None or self._current_document is None:
            return

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

        if rendered.content_format is ReaderContentFormat.MARKDOWN:
            self._show_markdown(rendered.content)
            return

        self._show_html(rendered.content, status if rendered.used_fallback else "")

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
            <article>{content_html}</article>
            <div class="reader-note">{safe_note}</div>
        """
        self.content.setHtml(self._wrap_html(body))

    def _show_markdown(self, markdown: str) -> None:
        if self._current_article is None:
            return

        title = self._current_article.title.replace("\n", " ")
        source = self._current_article.source_title.replace("\n", " ")
        note = self._reader_note.replace("\n", " ")
        document = (
            f"# {title}\n\n"
            f"*{self._source_label}: {source}*\n\n"
            f"{markdown}\n\n"
            f"> {note}"
        )
        self.content.document().setDefaultStyleSheet(
            "body { color: #d7e3ed; font-family: Georgia, serif; "
            "font-size: 18px; line-height: 1.62; } "
            "a { color: #69aefc; } pre, code { background: #0f2a3d; }"
        )
        self.content.setMarkdown(document)

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

        self.show_article(self._current_article)

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
                    font-size: 18px;
                    line-height: 1.62;
                    margin: 0;
                    padding: 32px 64px 72px;
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
                    font-size: 18px;
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
                article p {{
                    margin: 0 0 18px;
                }}
                article img {{
                    height: auto;
                    max-width: 100%;
                }}
                article table {{
                    border-collapse: collapse;
                    margin: 18px 0;
                    width: 100%;
                }}
                article th,
                article td {{
                    border: 1px solid #416074;
                    padding: 8px;
                    text-align: left;
                }}
                article pre,
                article code {{
                    background: #0f2a3d;
                    border-radius: 4px;
                    font-family: Consolas, "SFMono-Regular", monospace;
                }}
                article pre {{
                    overflow-wrap: anywhere;
                    padding: 14px;
                }}
                article a {{
                    color: #69aefc;
                }}
            </style>
        </head>
        <body>{body}</body>
        </html>
        """
