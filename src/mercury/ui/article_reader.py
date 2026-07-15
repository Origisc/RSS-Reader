from html import escape

from PySide6.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget

from mercury.models.article import Article


class ArticleReader(QWidget):
    """右侧文章阅读区域。"""

    def __init__(self) -> None:
        super().__init__()

        self.content = QTextBrowser()
        self.content.setOpenExternalLinks(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("阅读区"))
        layout.addWidget(self.content)

        self.show_welcome()

    def show_welcome(self) -> None:
        self.content.setHtml(
            """
            <h1>欢迎使用 Mercury</h1>
            <p>请从文章列表中选择一篇文章。</p>
            """
        )

    def show_article(self, article: Article) -> None:
        safe_title = escape(article.title)
        safe_source = escape(article.source_title)

        self.content.setHtml(
            f"""
            <h1>{safe_title}</h1>
            <p><strong>来源：</strong>{safe_source}</p>
            {article.content_html}
            """
        )