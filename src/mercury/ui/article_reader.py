from html import escape

from PySide6.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget

from mercury.models.article import Article


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

        self.title_label = QLabel()
        self.title_label.setObjectName("ReaderPanelTitle")
        self.content = QTextBrowser()
        self.content.setObjectName("ReaderContent")
        self.content.setOpenExternalLinks(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.title_label)
        layout.addWidget(self.content)

    def show_welcome(self) -> None:
        self._current_article = None
        body = (
            f"<h1>{escape(self._welcome_title)}</h1>"
            f"<p class='lede'>{escape(self._welcome_body)}</p>"
        )
        self.content.setHtml(self._wrap_html(body))

    def show_article(self, article: Article) -> None:
        self._current_article = article
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
            <article>{article.content_html}</article>
            <div class="reader-note">{safe_note}</div>
        """
        self.content.setHtml(self._wrap_html(body))

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
                .reader-note {{
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
                article p {{
                    margin: 0 0 18px;
                }}
            </style>
        </head>
        <body>{body}</body>
        </html>
        """
