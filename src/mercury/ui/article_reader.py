from html import escape

from PySide6.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget

from mercury.models.article import Article


class ArticleReader(QWidget):
    """右侧文章阅读区域。"""

    def __init__(self) -> None:
        super().__init__()

        self._current_article: Article | None = None
        self._welcome_title = ""
        self._welcome_body = ""
        self._source_label = ""

        self.title_label = QLabel()
        self.content = QTextBrowser()
        self.content.setOpenExternalLinks(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.title_label)
        layout.addWidget(self.content)

    def show_welcome(self) -> None:
        self._current_article = None
        self.content.setHtml(
            f"""
            <h1>{escape(self._welcome_title)}</h1>
            <p>{escape(self._welcome_body)}</p>
            """
        )

    def show_article(self, article: Article) -> None:
        self._current_article = article
        safe_title = escape(article.title)
        safe_source = escape(article.source_title)
        safe_source_label = escape(self._source_label)

        self.content.setHtml(
            f"""
            <h1>{safe_title}</h1>
            <p><strong>{safe_source_label}：</strong>{safe_source}</p>
            {article.content_html}
            """
        )

    def set_texts(
        self,
        title: str,
        welcome_title: str,
        welcome_body: str,
        source_label: str,
    ) -> None:
        self.title_label.setText(title)
        self._welcome_title = welcome_title
        self._welcome_body = welcome_body
        self._source_label = source_label

        if self._current_article is None:
            self.show_welcome()
            return

        self.show_article(self._current_article)
