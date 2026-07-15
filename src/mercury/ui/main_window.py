from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QToolBar,
)

from mercury.i18n import Translator
from mercury.i18n.translations import SUPPORTED_LANGUAGES
from mercury.services.article_service import ArticleService
from mercury.ui.article_list import ArticleList
from mercury.ui.article_reader import ArticleReader
from mercury.ui.settings_dialog import SettingsDialog
from mercury.ui.sidebar import Sidebar
from mercury.ui.theme import stylesheet_for_theme


class MainWindow(QMainWindow):
    """Mercury 主窗口。"""

    def __init__(self, article_service: ArticleService) -> None:
        super().__init__()

        self.article_service = article_service
        self.translator = Translator()
        self._theme = "system"

        self.resize(1200, 720)

        self.sidebar = Sidebar()
        self.article_list = ArticleList()
        self.article_reader = ArticleReader()

        self._setup_actions()
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_tool_bar()
        self._setup_ai_panel()
        self._connect_signals()
        self._load_initial_data()
        self._translate_ui()
        self._apply_theme()

    def _setup_ui(self) -> None:
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.article_list)
        self.splitter.addWidget(self.article_reader)

        self.splitter.setSizes([220, 320, 660])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setStretchFactor(2, 1)

        self.setCentralWidget(self.splitter)

    def _setup_actions(self) -> None:
        self.add_feed_action = QAction(self)
        self.add_feed_action.triggered.connect(
            lambda: self._show_pending_message("status.add_feed_pending")
        )

        self.refresh_action = QAction(self)
        self.refresh_action.triggered.connect(
            lambda: self._show_pending_message("status.refresh_pending")
        )

        self.exit_action = QAction(self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(QApplication.quit)

        self.open_settings_action = QAction(self)
        self.open_settings_action.setShortcut("Ctrl+,")
        self.open_settings_action.triggered.connect(self._open_settings)

        self.toggle_ai_action = QAction(self)
        self.toggle_ai_action.setCheckable(True)

        self.about_action = QAction(self)
        self.about_action.triggered.connect(self._show_about)

    def _setup_menu_bar(self) -> None:
        """创建主窗口菜单栏。"""
        self.file_menu = self.menuBar().addMenu("")
        self.settings_menu = self.menuBar().addMenu("")
        self.view_menu = self.menuBar().addMenu("")
        self.help_menu = self.menuBar().addMenu("")

        self.file_menu.addAction(self.add_feed_action)
        self.file_menu.addAction(self.refresh_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)
        self.settings_menu.addAction(self.open_settings_action)
        self.view_menu.addAction(self.toggle_ai_action)
        self.help_menu.addAction(self.about_action)

    def _setup_tool_bar(self) -> None:
        self.main_toolbar = QToolBar(self)
        self.main_toolbar.setObjectName("main_toolbar")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.main_toolbar)
        self.main_toolbar.addAction(self.add_feed_action)
        self.main_toolbar.addAction(self.refresh_action)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(self.toggle_ai_action)

    def _setup_ai_panel(self) -> None:
        self.ai_panel_label = QLabel()
        self.ai_panel_label.setWordWrap(True)
        self.ai_panel_label.setMargin(12)

        self.ai_dock = QDockWidget(self)
        self.ai_dock.setWidget(self.ai_panel_label)
        self.ai_dock.visibilityChanged.connect(
            self.toggle_ai_action.setChecked
        )
        self.toggle_ai_action.toggled.connect(self.ai_dock.setVisible)

        self.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea,
            self.ai_dock,
        )
        self.ai_dock.hide()

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
        dialog = SettingsDialog(
            self.translator,
            self.translator.language,
            self._theme,
            self,
        )

        if dialog.exec():
            self.translator.set_language(dialog.selected_language())
            self._theme = dialog.selected_theme()
            self._translate_ui()
            self._apply_theme()

            self.statusBar().showMessage(
                self.translator.text("status.settings_applied").format(
                    language=SUPPORTED_LANGUAGES[self.translator.language],
                    theme=self.translator.text(f"theme.{self._theme}"),
                ),
                5000,
            )

    def _show_about(self) -> None:
        """显示关于窗口。"""
        QMessageBox.about(
            self,
            self.translator.text("dialog.about.title"),
            self.translator.text("dialog.about.body"),
        )

    def _show_pending_message(self, message_key: str) -> None:
        message = self.translator.text(message_key)

        self.statusBar().showMessage(message, 5000)
        QMessageBox.information(
            self,
            self.translator.text("dialog.feature_pending.title"),
            message,
        )

    def _translate_ui(self) -> None:
        self.setWindowTitle(self.translator.text("app.title"))

        self.file_menu.setTitle(self.translator.text("menu.file"))
        self.settings_menu.setTitle(self.translator.text("menu.settings"))
        self.view_menu.setTitle(self.translator.text("menu.view"))
        self.help_menu.setTitle(self.translator.text("menu.help"))

        self.add_feed_action.setText(
            self.translator.text("action.add_feed")
        )
        self.refresh_action.setText(
            self.translator.text("action.refresh")
        )
        self.exit_action.setText(self.translator.text("action.exit"))
        self.open_settings_action.setText(
            self.translator.text("action.preferences")
        )
        self.toggle_ai_action.setText(
            self.translator.text("action.toggle_ai_panel")
        )
        self.about_action.setText(self.translator.text("action.about"))
        self.main_toolbar.setWindowTitle(
            self.translator.text("toolbar.main")
        )

        self.sidebar.set_title(self.translator.text("sidebar.title"))
        self.article_list.set_title(
            self.translator.text("article_list.title")
        )
        self.article_reader.set_texts(
            self.translator.text("article_reader.title"),
            self.translator.text("article_reader.welcome_title"),
            self.translator.text("article_reader.welcome_body"),
            self.translator.text("article_reader.source_label"),
        )

        self.ai_dock.setWindowTitle(self.translator.text("ai_panel.title"))
        self.ai_panel_label.setText(self.translator.text("ai_panel.body"))

    def _apply_theme(self) -> None:
        app = QApplication.instance()

        if app is None:
            return

        app.setStyleSheet(stylesheet_for_theme(self._theme))
