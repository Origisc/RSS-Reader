from collections.abc import Collection

from PySide6.QtCore import Qt, QRunnable, QThreadPool, QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
)

from mercury.agents import SummarySource, TranslationSource
from mercury.domain import TranslationResult
from mercury.i18n import Translator
from mercury.i18n.translations import SUPPORTED_LANGUAGES
from mercury.llm import InMemoryProviderConfigStore, ProviderConfigStore
from mercury.models.article import Article, Feed
from mercury.models.tag import Tag
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
from mercury.ui.shortcut_help import ShortcutEntry, ShortcutHelpDialog
from mercury.ui.sidebar import ALL_FEEDS_ID, STARRED_FEED_ID, Sidebar
from mercury.ui.summary_panel import (
    SummaryGenerator,
    SummaryPanel,
    SummaryResultLoader,
)
from mercury.ui.tag_panel import TagEditorPanel
from mercury.ui.theme import stylesheet_for_theme
from mercury.ui.translation_panel import (
    TranslationGenerator,
    TranslationPanel,
    TranslationResultLoader,
)


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
        translation_generator: TranslationGenerator | None = None,
        translation_result_loader: TranslationResultLoader | None = None,
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
        self._translation_generator = translation_generator
        self._translation_result_loader = translation_result_loader
        self._active_workers = set()
        self._selected_feed_id = ALL_FEEDS_ID
        self._selected_tag_ids: set[str] = set()
        self._tags: list[Tag] = []
        self._system_selected_article_id: str | None = None

        self.resize(1320, 820)

        self.sidebar = Sidebar()
        self.article_list = ArticleList()
        self.article_reader = ArticleReader()
        self.article_reader.set_reader_style(self._reader_style)

        self._setup_actions()
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_tag_panel()
        self._setup_summary_bar()
        self._setup_translation_bar()
        self._connect_signals()
        self._translate_ui()
        self._load_initial_data()
        self._apply_theme()

    def _setup_ui(self) -> None:
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName("MainSplitter")

        self.sidebar.setMinimumWidth(170)
        self.article_list.setMinimumWidth(230)
        self.article_reader.setMinimumWidth(540)

        self.reader_splitter = QSplitter(Qt.Orientation.Vertical)
        self.reader_splitter.setObjectName("ReaderSummarySplitter")
        self.reader_splitter.addWidget(self.article_reader)

        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.article_list)
        self.splitter.addWidget(self.reader_splitter)

        self.splitter.setSizes([185, 255, 880])
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

        self.toggle_summary_action = QAction(self)
        self.toggle_summary_action.setCheckable(True)
        self.toggle_summary_action.setChecked(False)
        self.toggle_summary_action.setShortcut("Ctrl+Shift+S")

        self.toggle_translation_action = QAction(self)
        self.toggle_translation_action.setCheckable(True)
        self.toggle_translation_action.setChecked(False)
        self.toggle_translation_action.setShortcut("Ctrl+Shift+T")

        self.shortcut_help_action = QAction(self)
        self.shortcut_help_action.setShortcut("F1")
        self.shortcut_help_action.triggered.connect(
            self._show_shortcut_help
        )

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
        self.view_menu.addAction(self.toggle_summary_action)
        self.view_menu.addAction(self.toggle_translation_action)
        self.help_menu.addAction(self.shortcut_help_action)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.about_action)

    def _setup_tag_panel(self) -> None:
        self.tag_editor = TagEditorPanel()
        self.tag_editor.close_requested.connect(
            lambda: self.toggle_tags_action.setChecked(False)
        )
        self.article_reader.set_overlay_widget(self.tag_editor)
        self.toggle_tags_action.toggled.connect(
            self._set_tag_panel_visible
        )

    def _set_tag_panel_visible(self, visible: bool) -> None:
        self.tag_editor.setVisible(visible)
        self.article_reader.set_tag_panel_visible(visible)

    def _setup_summary_bar(self) -> None:
        self.summary_panel = SummaryPanel(
            self.translator,
            generator=self._summary_generator,
            result_loader=self._summary_result_loader,
        )

        self.summary_section = QFrame()
        self.summary_section.setObjectName("SummarySection")

        self.summary_title_bar = QFrame()
        self.summary_title_bar.setObjectName("SummarySectionTitleBar")
        self.summary_title_button = QPushButton()
        self.summary_title_button.setObjectName("SummarySectionToggleButton")
        self.summary_title_button.clicked.connect(
            lambda: self.toggle_summary_action.setChecked(
                not self.toggle_summary_action.isChecked()
            )
        )

        title_layout = QHBoxLayout(self.summary_title_bar)
        title_layout.setContentsMargins(7, 2, 7, 2)
        title_layout.setSpacing(0)
        title_layout.addWidget(self.summary_title_button)
        title_layout.addStretch(1)

        section_layout = QVBoxLayout(self.summary_section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(0)
        section_layout.addWidget(self.summary_title_bar)
        section_layout.addWidget(self.summary_panel, 1)

        self.reader_splitter.addWidget(self.summary_section)
        self.reader_splitter.setSizes([570, 230])
        self.reader_splitter.setStretchFactor(0, 1)
        self.reader_splitter.setStretchFactor(1, 0)
        self.reader_splitter.setCollapsible(0, False)
        self.reader_splitter.setCollapsible(1, False)
        self._summary_section_height = 230

        self.toggle_summary_action.toggled.connect(
            self._set_summary_panel_visible
        )
        self._set_summary_panel_visible(False)

    def _set_summary_panel_visible(self, visible: bool) -> None:
        self._set_reader_section_visible(
            visible=visible,
            section=self.summary_section,
            title_bar=self.summary_title_bar,
            panel=self.summary_panel,
            stored_height_name="_summary_section_height",
        )
        self.article_reader.set_summary_panel_visible(visible)
        self._update_summary_title()

    def _update_summary_title(self) -> None:
        key = (
            "summary.collapse"
            if self.toggle_summary_action.isChecked()
            else "summary.expand"
        )
        self.summary_title_button.setText(self.translator.text(key))

    def _setup_translation_bar(self) -> None:
        self.translation_panel = TranslationPanel(
            self.translator,
            generator=self._translation_generator,
            result_loader=self._translation_result_loader,
        )
        self.article_reader.set_translation_controls_widget(
            self.translation_panel
        )

        self.toggle_translation_action.toggled.connect(
            self._set_translation_panel_visible
        )
        self._set_translation_panel_visible(False)

    def _set_translation_panel_visible(self, visible: bool) -> None:
        self.translation_panel.setVisible(visible)
        self.article_reader.set_translation_panel_visible(visible)

    def _set_reader_section_visible(
        self,
        *,
        visible: bool,
        section: QFrame,
        title_bar: QFrame,
        panel: QFrame,
        stored_height_name: str,
    ) -> None:
        index = self.reader_splitter.indexOf(section)
        sizes = self.reader_splitter.sizes()
        if index < 1 or index >= len(sizes):
            panel.setVisible(visible)
            return

        if (
            not visible
            and not panel.isHidden()
            and sizes[index] >= 180
        ):
            setattr(self, stored_height_name, sizes[index])

        combined_height = sizes[0] + sizes[index]
        panel.setVisible(visible)

        if visible:
            section.setMaximumHeight(16_777_215)
            section.setMinimumHeight(180)
            if combined_height > 1:
                preferred_height = int(
                    getattr(self, stored_height_name)
                )
                target_height = min(
                    preferred_height,
                    max(180, combined_height // 2),
                    combined_height - 1,
                )
                sizes[0] = max(1, combined_height - target_height)
                sizes[index] = target_height
                self.reader_splitter.setSizes(sizes)
            return

        section.setMinimumHeight(0)
        collapsed_height = title_bar.sizeHint().height()
        section.setMaximumHeight(collapsed_height)
        if combined_height > 0:
            sizes[0] = max(1, combined_height - collapsed_height)
            sizes[index] = collapsed_height
            self.reader_splitter.setSizes(sizes)

    def _connect_signals(self) -> None:
        self.sidebar.feed_selected.connect(self._show_feed_articles)
        self.sidebar.add_feed_requested.connect(self._add_feed)
        self.sidebar.import_opml_requested.connect(self._import_opml)
        self.sidebar.refresh_requested.connect(self._refresh_feeds)
        self.sidebar.delete_feeds_requested.connect(self._delete_feeds)
        self.sidebar.tag_filter_changed.connect(self._show_tagged_articles)
        self.sidebar.rename_tag_requested.connect(self._rename_tag)
        self.sidebar.delete_tag_requested.connect(self._delete_tag)
        self.article_list.article_selected.connect(self._show_article)
        self.article_list.star_toggled.connect(self._set_starred_state)
        self.article_list.translate_requested.connect(self._translate_current_article)
        self.article_list.translate_no_article.connect(self._show_translate_no_article)
        self.article_reader.read_state_change_requested.connect(
            self._set_read_state
        )
        self.article_reader.summary_panel_visibility_requested.connect(
            self.toggle_summary_action.setChecked
        )
        self.article_reader.translation_panel_visibility_requested.connect(
            self.toggle_translation_action.setChecked
        )
        self.article_reader.tag_panel_visibility_requested.connect(
            self.toggle_tags_action.setChecked
        )
        self.summary_panel.settings_requested.connect(
            self._open_ai_settings
        )
        self.translation_panel.settings_requested.connect(
            self._open_ai_settings
        )
        self.translation_panel.generation_progress.connect(
            self._show_translation_progress
        )
        self.translation_panel.generation_completed.connect(
            self._show_translation_result
        )
        self.tag_editor.add_tag_requested.connect(
            self._create_and_assign_tags
        )
        self.tag_editor.tag_assignment_changed.connect(
            self._set_article_tag_assignment
        )

    def _load_initial_data(self) -> None:
        feeds = self.article_service.list_feeds()
        all_articles = self.article_service.list_articles()
        feed_ids = {feed.id for feed in feeds}
        if (
            self._selected_feed_id
            not in {ALL_FEEDS_ID, STARRED_FEED_ID}
            and self._selected_feed_id not in feed_ids
        ):
            self._selected_feed_id = ALL_FEEDS_ID

        articles = self._articles_for_selection(self._selected_feed_id)
        unread_counts = self._unread_counts(feeds, all_articles)

        self.sidebar.set_feeds(
            feeds,
            unread_counts,
            self._safe_starred_count(),
        )
        self.sidebar.select_feed(self._selected_feed_id)
        self._reload_tags()
        if self._selected_tag_ids:
            try:
                articles = self.article_service.list_articles_by_tags(
                    sorted(self._selected_tag_ids)
                )
            except Exception:
                articles = []
        read_article_ids = self._read_article_ids(articles)
        self._update_article_list_title()
        self.article_list.set_articles(articles, read_article_ids)

        if not articles:
            self.article_reader.show_welcome()
            self.summary_panel.clear_article()
            self.translation_panel.clear_article()
            self._refresh_tag_editor()

    def _show_feed_articles(self, feed_id: str) -> None:
        self._selected_feed_id = feed_id
        self._selected_tag_ids.clear()
        self.sidebar.set_tags(self._tags)
        articles = self._articles_for_selection(feed_id)
        self._update_article_list_title()
        self.article_list.set_articles(
            articles,
            self._read_article_ids(articles),
        )
        self.article_reader.show_welcome()
        self.summary_panel.clear_article()
        self.translation_panel.clear_article()
        self._refresh_tag_editor()

    def _articles_for_selection(self, feed_id: str) -> list[Article]:
        if feed_id == STARRED_FEED_ID:
            try:
                return self.article_service.list_starred_articles()
            except Exception:
                self.statusBar().showMessage(
                    self.translator.text("status.star_failed"),
                    8000,
                )
                return []
        if feed_id == ALL_FEEDS_ID:
            return self.article_service.list_articles()
        return self.article_service.list_articles(feed_id)

    def _update_article_list_title(self) -> None:
        if self._selected_tag_ids:
            selected_names = [
                tag.name
                for tag in self._tags
                if tag.id in self._selected_tag_ids
            ]
            self.article_list.set_title(
                self.translator.text("article_list.tags_title").format(
                    tags=", ".join(selected_names),
                )
            )
            return

        key = (
            "article_list.starred_title"
            if self._selected_feed_id == STARRED_FEED_ID
            else "article_list.title"
        )
        self.article_list.set_title(self.translator.text(key))

    def _reload_tags(self) -> None:
        try:
            self._tags = self.article_service.list_tags()
        except Exception:
            self._tags = []
            self._selected_tag_ids.clear()

        available_ids = {tag.id for tag in self._tags}
        self._selected_tag_ids.intersection_update(available_ids)
        self.sidebar.set_tags(self._tags, self._selected_tag_ids)
        self._refresh_tag_editor(
            self.article_reader.current_article_id
        )

    def _refresh_tag_editor(
        self,
        article_id: str | None = None,
    ) -> None:
        if article_id is None:
            self.tag_editor.set_article_tags(
                self._tags,
                set(),
                article_available=False,
            )
            return

        try:
            assigned_ids = {
                tag.id
                for tag in self.article_service.list_article_tags(
                    article_id
                )
            }
        except Exception:
            assigned_ids = set()

        self.tag_editor.set_article_tags(
            self._tags,
            assigned_ids,
            article_available=True,
        )

    def _show_tagged_articles(
        self,
        tag_ids: tuple[str, ...],
    ) -> None:
        self._selected_tag_ids = {
            str(tag_id) for tag_id in tag_ids
        }
        if self._selected_tag_ids:
            try:
                articles = self.article_service.list_articles_by_tags(
                    sorted(self._selected_tag_ids)
                )
            except Exception:
                self.statusBar().showMessage(
                    self.translator.text("status.tag_failed"),
                    8000,
                )
                articles = []
        else:
            articles = self._articles_for_selection(
                self._selected_feed_id
            )

        self._update_article_list_title()
        self.article_list.set_articles(
            articles,
            self._read_article_ids(articles),
        )
        self.article_reader.show_welcome()
        self.summary_panel.clear_article()
        self.translation_panel.clear_article()
        self._refresh_tag_editor()

    def _create_and_assign_tags(self, raw_names: str) -> None:
        article_id = self.article_reader.current_article_id
        if article_id is None:
            return

        names = [
            value.strip()
            for value in raw_names.replace("\N{FULLWIDTH COMMA}", ",").split(
                ","
            )
            if value.strip()
        ]
        if not names:
            return

        try:
            for name in names:
                tag = self.article_service.create_tag(name)
                self.article_service.add_tag_to_article(
                    article_id,
                    tag.id,
                )
        except Exception:
            self.statusBar().showMessage(
                self.translator.text("status.tag_failed"),
                8000,
            )
            self._reload_tags()
            return

        self.tag_editor.clear_input()
        self._reload_tags()
        self._refresh_tagged_article_list()
        self.statusBar().showMessage(
            self.translator.text("status.tags_added"),
            5000,
        )

    def _set_article_tag_assignment(
        self,
        tag_id: str,
        assigned: bool,
    ) -> None:
        article_id = self.article_reader.current_article_id
        if article_id is None:
            return

        try:
            if assigned:
                self.article_service.add_tag_to_article(
                    article_id,
                    tag_id,
                )
            else:
                self.article_service.remove_tag_from_article(
                    article_id,
                    tag_id,
                )
        except Exception:
            self.statusBar().showMessage(
                self.translator.text("status.tag_failed"),
                8000,
            )
            self._refresh_tag_editor(article_id)
            return

        self._reload_tags()
        self._refresh_tagged_article_list()
        status_key = (
            "status.tag_assigned"
            if assigned
            else "status.tag_removed"
        )
        self.statusBar().showMessage(
            self.translator.text(status_key),
            5000,
        )

    def _rename_tag(self, tag_id: str) -> None:
        tag = next(
            (current for current in self._tags if current.id == tag_id),
            None,
        )
        if tag is None:
            return

        new_name, accepted = QInputDialog.getText(
            self,
            self.translator.text("tags.rename_dialog.title"),
            self.translator.text("tags.rename_dialog.label"),
            QLineEdit.EchoMode.Normal,
            tag.name,
        )
        if not accepted or not new_name.strip():
            return

        try:
            self.article_service.rename_tag(tag_id, new_name)
        except Exception:
            self.statusBar().showMessage(
                self.translator.text("status.tag_failed"),
                8000,
            )
            return

        self._reload_tags()
        self._update_article_list_title()
        self.statusBar().showMessage(
            self.translator.text("status.tag_renamed"),
            5000,
        )

    def _delete_tag(self, tag_id: str) -> None:
        tag = next(
            (current for current in self._tags if current.id == tag_id),
            None,
        )
        if tag is None or not self._confirm_tag_deletion(tag.name):
            return

        was_filtering = bool(self._selected_tag_ids)
        try:
            self.article_service.delete_tag(tag_id)
        except Exception:
            self.statusBar().showMessage(
                self.translator.text("status.tag_failed"),
                8000,
            )
            return

        self._selected_tag_ids.discard(tag_id)
        self._reload_tags()
        if was_filtering:
            self._show_tagged_articles(tuple(self._selected_tag_ids))
        self.statusBar().showMessage(
            self.translator.text("status.tag_deleted"),
            5000,
        )

    def _confirm_tag_deletion(self, tag_name: str) -> bool:
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle(
            self.translator.text("tags.delete_dialog.title")
        )
        dialog.setText(
            self.translator.text("tags.delete_dialog.body").format(
                name=tag_name,
            )
        )
        delete_button = dialog.addButton(
            self.translator.text("tags.delete"),
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

    def _refresh_tagged_article_list(self) -> None:
        if not self._selected_tag_ids:
            return
        self._show_tagged_articles(tuple(self._selected_tag_ids))

    def _ensure_article_processed(self, article_id: str) -> None:
        class _ArticleProcessorSignals(QObject):
            processed = Signal(str)
            finished = Signal()

        class _ArticleProcessor(QRunnable):
            def __init__(self, service, article_id):
                super().__init__()
                self.service = service
                self.article_id = article_id
                self.signals = _ArticleProcessorSignals()

            def run(self):
                try:
                    article = self.service.get_article(self.article_id)
                    if article is None:
                        return

                    if not article.original_html:
                        self.service.fetch_article_content(self.article_id)
                        article = self.service.get_article(self.article_id)
                        if article is None or not article.original_html:
                            return

                    if article.original_html and article.clean_status != "success":
                        self.service.clean_article_content(self.article_id)

                    self.signals.processed.emit(self.article_id)
                except Exception as e:
                    print(f"Error processing article {self.article_id}: {e}")
                finally:
                    self.signals.finished.emit()

        worker = _ArticleProcessor(self.article_service, article_id)
        worker.signals.processed.connect(self._on_article_processed)
        worker.signals.finished.connect(lambda: self._active_workers.discard(worker))
        self._active_workers.add(worker)
        QThreadPool.globalInstance().start(worker)

    def _on_article_processed(self, article_id: str) -> None:
        if self.article_reader.current_article_id != article_id:
            return

        article = self.article_service.get_article(article_id)
        if article is None:
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
        self.translation_panel.set_article(
            TranslationSource(
                article_id=article.id,
                title=article.title,
                raw_html=document.raw_html,
                cleaned_markdown=document.cleaned_markdown,
                cleaned_html=document.cleaned_html,
            )
        )

    def _show_article(self, article_id: str) -> None:
        system_selected = self._system_selected_article_id == article_id
        self._system_selected_article_id = None
        article = self.article_service.get_article(article_id)

        if article is None:
            self.article_reader.show_welcome()
            self.summary_panel.clear_article()
            self.translation_panel.clear_article()
            self._refresh_tag_editor()
            return

        self._ensure_article_processed(article_id)

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
        self.translation_panel.set_article(
            TranslationSource(
                article_id=article.id,
                title=article.title,
                raw_html=document.raw_html,
                cleaned_markdown=document.cleaned_markdown,
                cleaned_html=document.cleaned_html,
            )
        )
        self.article_reader.set_translation_result(
            self.translation_panel.displayed_result
        )
        self._refresh_tag_editor(article.id)
        if not system_selected:
            self._set_read_state(article.id, True, article)

    def _translate_current_article(self, article_id: str) -> None:
        article = self.article_service.get_article(article_id)
        if article is None:
            return

        if article.translated_title:
            return

        class _TitleTranslatorSignals(QObject):
            completed = Signal(str, bool, str)

        class _TitleTranslator(QRunnable):
            def __init__(self, service, article_id):
                super().__init__()
                self.service = service
                self.article_id = article_id
                self.signals = _TitleTranslatorSignals()

            def run(self):
                try:
                    result = self.service.translate_article_title(self.article_id)
                    success = "successfully" in result
                    self.signals.completed.emit(self.article_id, success, result)
                except Exception as e:
                    self.signals.completed.emit(self.article_id, False, str(e))

        worker = _TitleTranslator(self.article_service, article_id)
        worker.signals.completed.connect(self._on_title_translated)
        QThreadPool.globalInstance().start(worker)

    def _on_title_translated(self, article_id: str, success: bool, message: str) -> None:
        if self._selected_feed_id:
            articles = self._articles_for_selection(self._selected_feed_id)
            self.article_list.set_articles(
                articles,
                self._read_article_ids(articles),
            )
            current_id = self.article_list.current_article_id()
            if current_id:
                self._show_article(current_id)
        if not success:
            self.statusBar().showMessage(
                self.translator.text("status.translate_failed").format(message=message),
                8000,
            )

    def _show_translate_no_article(self) -> None:
        QMessageBox.information(
            self,
            self.translator.text("action.translate"),
            self.translator.text("article_list.translate.no_article"),
        )

    def _set_starred_state(
        self,
        article_id: str,
        is_starred: bool,
    ) -> None:
        visible_ids = self.article_list.visible_article_ids()
        selected_id = self.article_list.current_article_id()
        fallback_id = self._starred_selection_fallback(
            visible_ids,
            article_id,
            selected_id,
        )

        try:
            self.article_service.set_starred(article_id, is_starred)
        except Exception:
            self.statusBar().showMessage(
                self.translator.text("status.star_failed"),
                8000,
            )
            return

        if (
            self._selected_feed_id == STARRED_FEED_ID
            and not is_starred
        ):
            self.article_list.remove_article(article_id)

            if selected_id == article_id:
                if fallback_id is None:
                    self.article_reader.show_welcome()
                    self.summary_panel.clear_article()
                    self.translation_panel.clear_article()
                    self._refresh_tag_editor()
                else:
                    self._system_selected_article_id = fallback_id
                    if not self.article_list.select_article(fallback_id):
                        self._system_selected_article_id = None
        else:
            self.article_list.set_starred_state(
                article_id,
                is_starred,
            )

        self.sidebar.update_starred_count(
            self._safe_starred_count()
        )
        status_key = (
            "status.article_starred"
            if is_starred
            else "status.article_unstarred"
        )
        self.statusBar().showMessage(
            self.translator.text(status_key),
            5000,
        )

    def _safe_starred_count(self) -> int:
        try:
            return self.article_service.count_starred_articles()
        except Exception:
            return 0

    @staticmethod
    def _starred_selection_fallback(
        entry_ids: list[str],
        removing_entry_id: str,
        selected_entry_id: str | None,
    ) -> str | None:
        if selected_entry_id != removing_entry_id:
            return None
        if removing_entry_id not in entry_ids:
            return None

        index = entry_ids.index(removing_entry_id)
        if index + 1 < len(entry_ids):
            return entry_ids[index + 1]
        if index > 0:
            return entry_ids[index - 1]
        return None

    def _show_translation_progress(self, value: object) -> None:
        if not isinstance(value, TranslationResult):
            return

        if self.article_reader.current_article_id != value.article_id:
            return

        self.article_reader.set_translation_result(value)

    def _show_translation_result(self, value: object) -> None:
        if not isinstance(value, TranslationResult):
            return

        if self.article_reader.current_article_id != value.article_id:
            return

        self.article_reader.set_translation_result(value)
        self.toggle_translation_action.setChecked(False)

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
        self._refresh_feeds()

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
        self._refresh_feeds()

    def _refresh_feeds(self) -> None:
        self._run_service_action(
            self.article_service.refresh_all,
            self.translator.text("status.refresh_started"),
        )

    def _delete_feed(self, feed_id: str) -> None:
        self._delete_feeds((feed_id,))

    def _delete_feeds(self, feed_ids: Collection[str]) -> None:
        normalized_ids = tuple(
            dict.fromkeys(str(feed_id) for feed_id in feed_ids)
        )
        if not normalized_ids:
            return

        feeds_by_id = {
            feed.id: feed
            for feed in self.article_service.list_feeds()
        }
        feeds = [
            feeds_by_id[feed_id]
            for feed_id in normalized_ids
            if feed_id in feeds_by_id
        ]
        if len(feeds) != len(normalized_ids):
            return

        if self._feed_deletion_service is None:
            QMessageBox.information(
                self,
                self.translator.text("dialog.feature_pending.title"),
                self.translator.text("feed.delete_unavailable"),
            )
            return

        if len(feeds) == 1:
            confirmed = self._confirm_feed_deletion(feeds[0].title)
        else:
            confirmed = self._confirm_feeds_deletion(feeds)
        if not confirmed:
            return

        self.statusBar().showMessage(
            self.translator.text(
                "status.delete_feed_started"
                if len(feeds) == 1
                else "status.delete_feeds_started"
            ).format(count=len(feeds)),
            5000,
        )
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        try:
            if len(feeds) == 1:
                self._feed_deletion_service.delete_feed(feeds[0].id)
            else:
                self._feed_deletion_service.delete_feeds(
                    tuple(feed.id for feed in feeds)
                )
        except Exception:
            message = self.translator.text(
                "feed.delete_failed"
                if len(feeds) == 1
                else "feed.delete_many_failed"
            )
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
        self.translation_panel.clear_article()
        self.statusBar().showMessage(
            (
                self.translator.text(
                    "status.delete_feed_finished"
                ).format(title=feeds[0].title)
                if len(feeds) == 1
                else self.translator.text(
                    "status.delete_feeds_finished"
                ).format(count=len(feeds))
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

    def _confirm_feeds_deletion(self, feeds: Collection[Feed]) -> bool:
        feed_list = list(feeds)
        titles = "\n".join(f"• {feed.title}" for feed in feed_list)
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle(
            self.translator.text("feed.delete_many_dialog.title")
        )
        dialog.setText(
            self.translator.text("feed.delete_many_dialog.body").format(
                count=len(feed_list),
                titles=titles,
            )
        )
        delete_button = dialog.addButton(
            self.translator.text("action.delete_feeds"),
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
        try:
            current_config = self._provider_config_store.load()
        except Exception:
            message = self.translator.text(
                "status.ai_settings_storage_failed"
            )
            QMessageBox.warning(
                self,
                self.translator.text("dialog.feature_failed.title"),
                message,
            )
            self.statusBar().showMessage(message, 8000)
            return

        dialog = AISettingsDialog(
            self.translator,
            current_config=current_config,
            connection_tester=self._provider_connection_tester,
            parent=self,
        )

        if dialog.exec():
            try:
                self._provider_config_store.save(
                    dialog.selected_config()
                )
            except Exception:
                message = self.translator.text(
                    "status.ai_settings_storage_failed"
                )
                QMessageBox.warning(
                    self,
                    self.translator.text("dialog.feature_failed.title"),
                    message,
                )
                self.statusBar().showMessage(message, 8000)
                return
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

    def _show_shortcut_help(self) -> None:
        dialog = ShortcutHelpDialog(
            self.translator,
            self._shortcut_entries(),
            self,
        )
        dialog.exec()

    def _shortcut_entries(self) -> tuple[ShortcutEntry, ...]:
        shortcut_actions = (
            action
            for action in self.findChildren(QAction)
            if not action.shortcut().isEmpty()
        )
        return tuple(
            ShortcutEntry(
                action.shortcut().toString(),
                action.statusTip() or action.text(),
            )
            for action in shortcut_actions
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
        self.toggle_summary_action.setText(
            self.translator.text("action.toggle_summary_panel")
        )
        self.toggle_translation_action.setText(
            self.translator.text("action.toggle_translation_panel")
        )
        self.shortcut_help_action.setText(
            self.translator.text("action.shortcuts")
        )
        self.about_action.setText(self.translator.text("action.about"))
        shortcut_descriptions = (
            (
                self.shortcut_help_action,
                self.translator.text("shortcuts.show_help"),
            ),
            (
                self.open_settings_action,
                self.translator.text("shortcuts.open_settings"),
            ),
            (
                self.toggle_summary_action,
                self.translator.text("shortcuts.toggle_summary"),
            ),
            (
                self.toggle_translation_action,
                self.translator.text("shortcuts.toggle_translation"),
            ),
            (
                self.exit_action,
                self.translator.text("shortcuts.exit"),
            ),
        )
        for action, description in shortcut_descriptions:
            action.setStatusTip(description)
            action.setToolTip(description)

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
            batch_delete=self.translator.text(
                "action.multi_select_feeds"
            ),
            delete_selected=self.translator.text(
                "action.delete_selected_feeds"
            ),
            cancel_selection=self.translator.text("settings.cancel"),
        )
        self.sidebar.set_footer(self.translator.text("sidebar.footer"))
        self.sidebar.set_feed_detail_text(
            self.translator.text("sidebar.feed_detail")
        )
        self.sidebar.set_virtual_feed_texts(
            all_feeds=self.translator.text("sidebar.all_feeds"),
            starred=self.translator.text("sidebar.starred"),
            starred_detail=self.translator.text(
                "sidebar.starred_detail"
            ),
        )
        self.sidebar.set_tag_browser_texts(
            self.translator.text("tags.title"),
            self.translator.text("tags.browser_hint"),
            clear_filter=self.translator.text("tags.filter_clear"),
            rename=self.translator.text("tags.rename"),
            delete=self.translator.text("tags.delete"),
        )
        self.sidebar.set_tags(self._tags, self._selected_tag_ids)
        self._update_article_list_title()
        self.article_list.set_filter_text(
            self.translator.text("article_list.unread_filter")
        )
        self.article_list.set_translate_text(
            self.translator.text("article_list.translate")
        )
        self.article_list.set_star_texts(
            star=self.translator.text("action.star"),
            unstar=self.translator.text("action.unstar"),
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
        self.article_reader.set_summary_toggle_texts(
            text=self.translator.text("reader.summary_toggle"),
            tooltip=self.translator.text("reader.summary_toggle_tooltip"),
        )
        self.article_reader.set_translation_toggle_texts(
            text=self.translator.text("reader.translation_toggle"),
            tooltip=self.translator.text(
                "reader.translation_toggle_tooltip"
            ),
        )
        self.article_reader.set_translation_view_texts(
            show_bilingual=self.translator.text(
                "reader.translation_view.bilingual"
            ),
            show_original=self.translator.text(
                "reader.translation_view.original"
            ),
            available_tooltip=self.translator.text(
                "reader.translation_view.available_tooltip"
            ),
            unavailable_tooltip=self.translator.text(
                "reader.translation_view.unavailable_tooltip"
            ),
            status=self.translator.text(
                "reader.status.bilingual"
            ),
            translation_unavailable=self.translator.text(
                "translation.paragraph.unavailable"
            ),
            translation_translating=self.translator.text(
                "translation.paragraph.translating"
            ),
        )
        self.article_reader.set_tag_toggle_texts(
            text=self.translator.text("reader.tags_toggle"),
            tooltip=self.translator.text("reader.tags_toggle_tooltip"),
        )

        self.tag_editor.set_texts(
            title=self.translator.text("tags.title"),
            input_placeholder=self.translator.text("tags.input_placeholder"),
            add=self.translator.text("tags.add"),
            existing=self.translator.text("tags.existing"),
            empty=self.translator.text("tags.empty"),
            no_article=self.translator.text("tags.no_article"),
            close_tooltip=self.translator.text("tags.close"),
        )

        self._update_summary_title()
        self.summary_title_button.setToolTip(
            self.translator.text("reader.summary_toggle_tooltip")
        )
        self.summary_panel.set_translator(self.translator)
        self.translation_panel.set_translator(self.translator)

    def _apply_theme(self) -> None:
        app = QApplication.instance()

        if app is None:
            return

        app.setStyleSheet(stylesheet_for_theme(self._theme))
        self.article_list.set_color_scheme(self._theme)
        self.summary_panel.set_color_scheme(self._theme)
        self.translation_panel.set_color_scheme(self._theme)
