from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QSplitter

from mercury.services.article_service import ArticleService
from mercury.ui.article_list import ArticleList
from mercury.ui.article_reader import ArticleReader
from mercury.ui.sidebar import Sidebar


class MainWindow(QMainWindow):
    """Mercury 主窗口。"""

    def __init__(self, article_service: ArticleService) -> None:
        super().__init__()

        self.article_service = article_service

        self.setWindowTitle("Mercury")
        self.resize(1200, 720)

        self.sidebar = Sidebar()
        self.article_list = ArticleList()
        self.article_reader = ArticleReader()

        self._setup_ui()
        self._connect_signals()
        self._load_initial_data()

    def _setup_ui(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal)

        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.article_list)
        splitter.addWidget(self.article_reader)

        splitter.setSizes([220, 320, 660])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 0)
        splitter.setStretchFactor(2, 1)

        self.setCentralWidget(splitter)

    def _connect_signals(self) -> None:
        self.sidebar.feed_selected.connect(self._show_feed_articles)
        self.article_list.article_selected.connect(self._show_article)

    def _load_initial_data(self) -> None:
        feeds = self.article_service.list_feeds()
        articles = self.article_service.list_articles()

        self.sidebar.set_feeds(feeds)
        self.article_list.set_articles(articles)

    def _show_feed_articles(self, feed_id: str) -> None:
        articles = self.article_service.list_articles(feed_id)
        self.article_list.set_articles(articles)
        self.article_reader.show_welcome()

    def _show_article(self, article_id: str) -> None:
        article = self.article_service.get_article(article_id)

        if article is None:
            self.article_reader.show_welcome()
            return

        self.article_reader.show_article(article)