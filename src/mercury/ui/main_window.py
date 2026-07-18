from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QToolBar,
    QVBoxLayout,
)

from mercury.agents import SummarySource
from mercury.i18n import Translator
from mercury.i18n.translations import SUPPORTED_LANGUAGES
from mercury.llm import InMemoryProviderConfigStore, ProviderConfigStore
from mercury.models.article import Article, Feed
from mercury.services.article_service import ArticleService
from mercury.ui.ai_settings import AISettingsDialog, ConnectionTester
from mercury.ui.article_list import ArticleList
from mercury.ui.article_reader import ArticleReader
from mercury.ui.feed_deletion import FeedDeletionService
from mercury.ui.read_state import InMemoryReadStateStore, ReadStateStore
from mercury.ui.reader_document import ReaderDocument
from mercury.ui.reader_style import (
    InMemoryReaderStyleStore,
    ReaderStyle,
    ReaderStyleStore,
)
from mercury.ui.settings_dialog import SettingsDialog
from mercury.ui.sidebar import Sidebar
from mercury.ui.summary_panel import (
    SummaryGenerator,
    SummaryPanel,
    SummaryResultLoader,
)
from mercury.ui.theme import stylesheet_for_theme


class MainWindow(QMainWindow):
    """Mercury 主窗口。"""

    def __init__(
        self,
        article_service: ArticleService,
        reader_style_store: ReaderStyleStore | None = None,
        read_state_store: ReadStateStore | None = None,
        feed_deletion_service: FeedDeletionService | None = None,
        provider_config_store: ProviderConfigStore | None = None,
        provider_connection_tester: ConnectionTester | None = None,
        summary_generator: SummaryGenerator | None = None,
        summary_result_loader: SummaryResultLoader | None = None,
    ) -> None:
        super().__init__()

        self.setObjectName("MercuryWindow")
        self.article_service = article_service
        self.translator = Translator()
        self._theme = "dark"
        self._reader_style_store = (
            reader_style_store or InMemoryReaderStyleStore()
        )
        self._reader_style = self._reader_style_store.load().normalized()
        self._read_state_store = read_state_store or InMemoryReadStateStore()
        self._feed_deletion_service = feed_deletion_service
        self._provider_config_store = (
            provider_config_store
            if provider_config_store is not None
            else InMemoryProviderConfigStore()
        )
        self._provider_connection_tester = provider_connection_tester
        self._summary_generator = summary_generator
        self._summary_result_loader = summary_result_loader

        self.resize(1320, 820)

        self.sidebar = Sidebar()
        self.article_list = ArticleList()
        self.article_reader = ArticleReader()
        self.article_reader.set_reader_style(self._reader_style)

        self._setup_actions()
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_tool_bar()
        self._setup_tag_panel()
        self._setup_summary_bar()
        self._connect_signals()
        self._translate_ui()
        self._load_initial_data()
        self._apply_theme()

    def _setup_ui(self) -> None:
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName("MainSplitter")

        self.sidebar.setMinimumWidth(190)
        self.article_list.setMinimumWidth(250)
        self.article_reader.setMinimumWidth(560)

        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.article_list)
        self.splitter.addWidget(self.article_reader)

        self.splitter.setSizes([210, 270, 840])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setStretchFactor(2, 1)

        self.setCentralWidget(self.splitter)

    def _setup_actions(self) -> None:
        self.add_feed_action = QAction(self)
        self.add_feed_action.triggered.connect(self._add_feed)

        self.import_opml_action = QAction(self)
        self.import_opml_action.triggered.connect(self._import_opml)

        self.refresh_action = QAction(self)
        self.refresh_action.triggered.connect(self._refresh_feeds)

        self.exit_action = QAction(self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(QApplication.quit)

        self.open_settings_action = QAction(self)
        self.open_settings_action.setShortcut("Ctrl+,")
        self.open_settings_action.triggered.connect(self._open_settings)

        self.open_ai_settings_action = QAction(self)
        self.open_ai_settings_action.triggered.connect(
            self._open_ai_settings
        )

        self.toggle_tags_action = QAction(self)
        self.toggle_tags_action.setCheckable(True)
        self.toggle_tags_action.setChecked(True)

        self.about_action = QAction(self)
        self.about_action.triggered.connect(self._show_about)

    def _setup_menu_bar(self) -> None:
        """创建主窗口菜单栏。"""
        self.file_menu = self.menuBar().addMenu("")
        self.settings_menu = self.menuBar().addMenu("")
        self.view_menu = self.menuBar().addMenu("")
        self.help_menu = self.menuBar().addMenu("")

        self.file_menu.addAction(self.add_feed_action)
        self.file_menu.addAction(self.import_opml_action)
        self.file_menu.addAction(self.refresh_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)
        self.settings_menu.addAction(self.open_settings_action)
        self.settings_menu.addAction(self.open_ai_settings_action)
        self.view_menu.addAction(self.toggle_tags_action)
        self.help_menu.addAction(self.about_action)

    def _setup_tool_bar(self) -> None:
        self.main_toolbar = QToolBar(self)
        self.main_toolbar.setObjectName("AppToolbar")
        self.main_toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.main_toolbar)
        self.main_toolbar.addAction(self.add_feed_action)
        self.main_toolbar.addAction(self.import_opml_action)
        self.main_toolbar.addAction(self.refresh_action)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(self.toggle_tags_action)

    def _setup_tag_panel(self) -> None:
        panel = QFrame()
        panel.setObjectName("TagPanel")

        self.tags_title_label = QLabel()
        self.tags_title_label.setObjectName("TagPanelTitle")
        self.tag_input_label = QLabel()
        self.tag_input_label.setObjectName("TagInputPlaceholder")
        self.tag_add_button = QPushButton()
        self.tag_add_button.setObjectName("TagAddButton")
        self.tag_add_button.setEnabled(False)
        self.suggested_label = QLabel()
        self.suggested_label.setObjectName("TagSectionTitle")
        self.existing_label = QLabel()
        self.existing_label.setObjectName("TagSectionTitle")
        self.no_tags_label = QLabel()
        self.no_tags_label.setObjectName("TagEmpty")

        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(6)
        input_layout.addWidget(self.tag_input_label, 1)
        input_layout.addWidget(self.tag_add_button)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(9)
        layout.addWidget(self.tags_title_label)
        layout.addLayout(input_layout)
        layout.addWidget(self.suggested_label)
        layout.addLayout(
            self._chip_row(["History", "Internet", "AOL", "America"])
        )
        layout.addWidget(self.existing_label)
        layout.addLayout(
            self._chip_row(["AI", "Programming", "Open Source", "Apple"])
        )
        layout.addLayout(
            self._chip_row(["Politics", "Hardware", "Business", "Writing"])
        )
        layout.addWidget(self.no_tags_label)
        layout.addStretch(1)

        self.tags_dock = QDockWidget(self)
        self.tags_dock.setObjectName("TagsDock")
        self.tags_dock.setWidget(panel)
        self.tags_dock.visibilityChanged.connect(
            self.toggle_tags_action.setChecked
        )
        self.toggle_tags_action.toggled.connect(self.tags_dock.setVisible)

        self.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea,
            self.tags_dock,
        )

    def _setup_summary_bar(self) -> None:
        self.summary_panel = SummaryPanel(
            self.translator,
            generator=self._summary_generator,
            result_loader=self._summary_result_loader,
        )

        self.summary_dock = QDockWidget(self)
        self.summary_dock.setObjectName("SummaryDock")
        self.summary_dock.setMinimumHeight(210)
        self.summary_dock.setWidget(self.summary_panel)
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea,
            self.summary_dock,
        )

    def _chip_row(self, labels: list[str]) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        for label_text in labels:
            chip = QLabel(label_text)
            chip.setProperty("chip", True)
            row.addWidget(chip)

        row.addStretch(1)
        return row

    def _connect_signals(self) -> None:
        self.sidebar.feed_selected.connect(self._show_feed_articles)
        self.sidebar.add_feed_requested.connect(self._add_feed)
        self.sidebar.import_opml_requested.connect(self._import_opml)
        self.sidebar.refresh_requested.connect(self._refresh_feeds)
        self.sidebar.delete_feed_requested.connect(self._delete_feed)
        self.article_list.article_selected.connect(self._show_article)
        self.article_reader.read_state_change_requested.connect(
            self._set_read_state
        )
        self.summary_panel.settings_requested.connect(
            self._open_ai_settings
        )

    def _load_initial_data(self) -> None:
        feeds = self.article_service.list_feeds()
        articles = self.article_service.list_articles()
        read_article_ids = self._read_article_ids(articles)
        unread_counts = self._unread_counts(feeds, articles)

        self.sidebar.set_feeds(feeds, unread_counts)
        self.article_list.set_articles(articles, read_article_ids)

        if not articles:
            self.article_reader.show_welcome()
            self.summary_panel.clear_article()

    def _show_feed_articles(self, feed_id: str) -> None:
        articles = self.article_service.list_articles(feed_id)
        self.article_list.set_articles(
            articles,
            self._read_article_ids(articles),
        )
        self.article_reader.show_welcome()
        self.summary_panel.clear_article()

    def _show_article(self, article_id: str) -> None:
        article = self.article_service.get_article(article_id)

        if article is None:
            self.article_reader.show_welcome()
            self.summary_panel.clear_article()
            return

        document = ReaderDocument.from_article(article)
        self.article_reader.show_article(article, document)
        self.summary_panel.set_article(
            SummarySource(
                article_id=article.id,
                title=article.title,
                raw_html=document.raw_html,
                cleaned_markdown=document.cleaned_markdown,
                cleaned_html=document.cleaned_html,
            )
        )
        self._set_read_state(article.id, True, article)

    def _set_read_state(
        self,
        article_id: str,
        is_read: bool,
        article: Article | None = None,
    ) -> None:
        article = article or self.article_service.get_article(article_id)

        if article is None:
            return

        self._read_state_store.set_read(article_id, is_read)
        self.article_list.set_read_state(article_id, is_read)

        if self.article_reader.current_article_id == article_id:
            self.article_reader.set_read_state(is_read)

        unread_count = sum(
            not self._read_state_store.is_read(current.id)
            for current in self.article_service.list_articles(article.feed_id)
        )
        self.sidebar.update_unread_count(article.feed_id, unread_count)

    def _read_article_ids(self, articles: list[Article]) -> set[str]:
        return {
            article.id
            for article in articles
            if self._read_state_store.is_read(article.id)
        }

    def _unread_counts(
        self,
        feeds: list[Feed],
        articles: list[Article],
    ) -> dict[str, int]:
        counts = {feed.id: 0 for feed in feeds}

        for article in articles:
            if not self._read_state_store.is_read(article.id):
                counts[article.feed_id] = counts.get(article.feed_id, 0) + 1

        return counts

    def _add_feed(self) -> None:
        xml_url, accepted = QInputDialog.getText(
            self,
            self.translator.text("feed.add_dialog.title"),
            self.translator.text("feed.add_dialog.label"),
            QLineEdit.EchoMode.Normal,
            "",
        )

        if not accepted or not xml_url.strip():
            return

        self._run_service_action(
            lambda: self.article_service.add_feed(xml_url.strip()),
            self.translator.text("status.add_feed_started"),
        )

    def _import_opml(self) -> None:
        file_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            self.translator.text("opml.import_dialog.title"),
            "",
            self.translator.text("opml.import_dialog.filter"),
        )

        if not file_path:
            return

        self._run_service_action(
            lambda: self.article_service.import_opml(file_path),
            self.translator.text("status.import_opml_started"),
        )

    def _refresh_feeds(self) -> None:
        self._run_service_action(
            self.article_service.refresh_all,
            self.translator.text("status.refresh_started"),
        )

    def _delete_feed(self, feed_id: str) -> None:
        feed = next(
            (
                current
                for current in self.article_service.list_feeds()
                if current.id == feed_id
            ),
            None,
        )

        if feed is None:
            return

        if self._feed_deletion_service is None:
            QMessageBox.information(
                self,
                self.translator.text("dialog.feature_pending.title"),
                self.translator.text("feed.delete_unavailable"),
            )
            return

        if not self._confirm_feed_deletion(feed.title):
            return

        self.statusBar().showMessage(
            self.translator.text("status.delete_feed_started"),
            5000,
        )
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        try:
            self._feed_deletion_service.delete_feed(feed_id)
        except Exception:
            message = self.translator.text("feed.delete_failed")
            QMessageBox.warning(
                self,
                self.translator.text("dialog.feature_failed.title"),
                message,
            )
            self.statusBar().showMessage(message, 8000)
            return
        finally:
            QApplication.restoreOverrideCursor()

        self._load_initial_data()
        self.article_reader.show_welcome()
        self.summary_panel.clear_article()
        self.statusBar().showMessage(
            self.translator.text("status.delete_feed_finished").format(
                title=feed.title,
            ),
            8000,
        )

    def _confirm_feed_deletion(self, feed_title: str) -> bool:
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle(
            self.translator.text("feed.delete_dialog.title")
        )
        dialog.setText(
            self.translator.text("feed.delete_dialog.body").format(
                title=feed_title,
            )
        )
        delete_button = dialog.addButton(
            self.translator.text("action.delete_feed"),
            QMessageBox.ButtonRole.DestructiveRole,
        )
        cancel_button = dialog.addButton(
            self.translator.text("settings.cancel"),
            QMessageBox.ButtonRole.RejectRole,
        )
        dialog.setDefaultButton(cancel_button)
        dialog.setEscapeButton(cancel_button)
        dialog.exec()
        return dialog.clickedButton() is delete_button

    def _run_service_action(self, action, started_message: str) -> None:
        self.statusBar().showMessage(started_message, 5000)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        try:
            message = action()
        except Exception as exc:
            QMessageBox.warning(
                self,
                self.translator.text("dialog.feature_failed.title"),
                str(exc),
            )
            self.statusBar().showMessage(str(exc), 8000)
            return
        finally:
            QApplication.restoreOverrideCursor()

        self._load_initial_data()
        self.statusBar().showMessage(message, 8000)

    def _open_settings(self) -> None:
        """打开设置窗口。"""
        dialog = SettingsDialog(
            self.translator,
            self.translator.language,
            self._theme,
            current_reader_style=self._reader_style,
            parent=self,
        )

        if dialog.exec():
            self._apply_settings(
                dialog.selected_language(),
                dialog.selected_theme(),
                dialog.selected_reader_style(),
            )

            self.statusBar().showMessage(
                self.translator.text("status.settings_applied").format(
                    language=SUPPORTED_LANGUAGES[self.translator.language],
                    theme=self.translator.text(f"theme.{self._theme}"),
                    font_size=self._reader_style.font_size,
                ),
                5000,
            )

    def _open_ai_settings(self) -> None:
        dialog = AISettingsDialog(
            self.translator,
            current_config=self._provider_config_store.load(),
            connection_tester=self._provider_connection_tester,
            parent=self,
        )

        if dialog.exec():
            self._provider_config_store.save(dialog.selected_config())
            self.statusBar().showMessage(
                self.translator.text("status.ai_settings_saved"),
                5000,
            )

    def _apply_settings(
        self,
        language: str,
        theme: str,
        reader_style: ReaderStyle,
    ) -> None:
        """Apply presentation settings without replacing UI data or selection."""
        self.translator.set_language(language)
        self._theme = theme
        self._reader_style = reader_style.normalized()
        self._reader_style_store.save(self._reader_style)
        self.article_reader.set_reader_style(self._reader_style)
        self._translate_ui()
        self._apply_theme()

    def _show_about(self) -> None:
        """显示关于窗口。"""
        QMessageBox.about(
            self,
            self.translator.text("dialog.about.title"),
            self.translator.text("dialog.about.body"),
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
        self.import_opml_action.setText(
            self.translator.text("action.import_opml")
        )
        self.refresh_action.setText(
            self.translator.text("action.refresh")
        )
        self.exit_action.setText(self.translator.text("action.exit"))
        self.open_settings_action.setText(
            self.translator.text("action.preferences")
        )
        self.open_ai_settings_action.setText(
            self.translator.text("action.ai_settings")
        )
        self.toggle_tags_action.setText(
            self.translator.text("action.toggle_tags_panel")
        )
        self.about_action.setText(self.translator.text("action.about"))
        self.main_toolbar.setWindowTitle(
            self.translator.text("toolbar.main")
        )

        self.sidebar.set_title(self.translator.text("sidebar.title"))
        self.sidebar.set_tabs(
            self.translator.text("sidebar.tab.feeds"),
            self.translator.text("sidebar.tab.tags"),
        )
        self.sidebar.set_action_texts(
            add_feed=self.translator.text("action.add_feed"),
            import_opml=self.translator.text("action.import_opml"),
            refresh=self.translator.text("action.refresh"),
            delete_feed=self.translator.text("action.delete_feed"),
        )
        self.sidebar.set_footer(self.translator.text("sidebar.footer"))
        self.sidebar.set_feed_detail_text(
            self.translator.text("sidebar.feed_detail")
        )
        self.article_list.set_title(
            self.translator.text("article_list.title")
        )
        self.article_list.set_entry_meta_text(
            self.translator.text("article_list.entry_meta")
        )
        self.article_reader.set_texts(
            self.translator.text("article_reader.title"),
            self.translator.text("article_reader.welcome_title"),
            self.translator.text("article_reader.welcome_body"),
            self.translator.text("article_reader.source_label"),
            self.translator.text("article_reader.local_note"),
        )
        self.article_reader.set_view_texts(
            raw_label=self.translator.text("reader.view.raw"),
            cleaned_html_label=self.translator.text(
                "reader.view.cleaned_html"
            ),
            markdown_label=self.translator.text("reader.view.markdown"),
            raw_status=self.translator.text("reader.status.raw"),
            cleaned_html_status=self.translator.text(
                "reader.status.cleaned_html"
            ),
            markdown_status=self.translator.text("reader.status.markdown"),
            fallback_unavailable=self.translator.text(
                "reader.status.fallback_unavailable"
            ),
            fallback_error=self.translator.text("reader.status.fallback_error"),
        )
        self.article_reader.set_read_state_texts(
            mark_read=self.translator.text("action.mark_read"),
            mark_unread=self.translator.text("action.mark_unread"),
        )

        self.tags_dock.setWindowTitle(self.translator.text("tags.title"))
        self.tags_title_label.setText(self.translator.text("tags.title"))
        self.tag_input_label.setText(
            self.translator.text("tags.input_placeholder")
        )
        self.tag_add_button.setText(self.translator.text("tags.add"))
        self.suggested_label.setText(self.translator.text("tags.suggested"))
        self.existing_label.setText(self.translator.text("tags.existing"))
        self.no_tags_label.setText(self.translator.text("tags.empty"))

        self.summary_dock.setWindowTitle(
            self.translator.text("summary.title")
        )
        self.summary_panel.set_translator(self.translator)

    def _apply_theme(self) -> None:
        app = QApplication.instance()

        if app is None:
            return

        app.setStyleSheet(stylesheet_for_theme(self._theme))
        self.article_list.set_color_scheme(self._theme)
