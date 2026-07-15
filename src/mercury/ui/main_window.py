from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QSplitter,
)

from mercury.services.article_service import ArticleService
from mercury.ui.article_list import ArticleList
from mercury.ui.article_reader import ArticleReader
from mercury.ui.settings_dialog import SettingsDialog
from mercury.ui.sidebar import Sidebar

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
        self._setup_menu_bar()
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

    def _setup_menu_bar(self) -> None:
        """创建主窗口菜单栏。"""
        file_menu = self.menuBar().addMenu("文件")
        settings_menu = self.menuBar().addMenu("设置")
        help_menu = self.menuBar().addMenu("帮助")

        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(QApplication.quit)

        open_settings_action = QAction("首选项", self)
        open_settings_action.setShortcut("Ctrl+,")
        open_settings_action.triggered.connect(self._open_settings)

        about_action = QAction("关于 Mercury", self)
        about_action.triggered.connect(self._show_about)

        file_menu.addAction(exit_action)
        settings_menu.addAction(open_settings_action)
        help_menu.addAction(about_action)

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
    
    def _open_settings(self) -> None:
        """打开设置窗口。"""
        dialog = SettingsDialog(self)

        if dialog.exec():
            language = dialog.selected_language()
            theme = dialog.selected_theme()

            self.statusBar().showMessage(
                f"已选择语言：{language}，主题：{theme}",
                5000,
            )

    def _show_about(self) -> None:
        """显示关于窗口。"""
        QMessageBox.about(
            self,
            "关于 Mercury",
            (
                "<h2>Mercury</h2>"
                "<p>一款本地优先、跨平台的 RSS 阅读器。</p>"
                "<p>当前版本：UI 开发原型</p>"
            ),
        )