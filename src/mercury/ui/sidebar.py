from collections.abc import Collection, Mapping

from PySide6.QtCore import QRectF, QSignalBlocker, Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from mercury.models.article import Feed
from mercury.models.tag import Tag
from mercury.ui.star_icon import draw_star


FEED_ID_ROLE = Qt.ItemDataRole.UserRole
FEED_TITLE_ROLE = Qt.ItemDataRole.UserRole + 1
UNREAD_COUNT_ROLE = Qt.ItemDataRole.UserRole + 2
IS_VIRTUAL_ROLE = Qt.ItemDataRole.UserRole + 3
STARRED_COUNT_ROLE = Qt.ItemDataRole.UserRole + 4
TAG_ID_ROLE = Qt.ItemDataRole.UserRole + 5
TAG_NAME_ROLE = Qt.ItemDataRole.UserRole + 6
TAG_COUNT_ROLE = Qt.ItemDataRole.UserRole + 7

ALL_FEEDS_ID = "__all__"
STARRED_FEED_ID = "__starred__"


class Sidebar(QWidget):
    """左侧订阅源区域。"""

    feed_selected = Signal(str)
    add_feed_requested = Signal()
    import_opml_requested = Signal()
    refresh_requested = Signal()
    delete_feed_requested = Signal(str)
    delete_feeds_requested = Signal(object)
    tag_filter_changed = Signal(object)
    rename_tag_requested = Signal(str)
    delete_tag_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("SidebarPanel")
        self._feed_detail_text = "{count} unread"
        self._starred_detail_text = "{count} starred"
        self._footer_template = "Feeds: {feeds} · Unread: {unread}"
        self._all_feeds_text = "All Feeds"
        self._starred_text = "Starred"
        self._feed_count = 0
        self._unread_total = 0
        self._starred_total = 0
        self._clear_tag_filter_text = "Clear filter"
        self._rename_tag_text = "Rename"
        self._delete_tag_text = "Delete"
        self._batch_delete_mode = False
        self._feed_id_before_batch: str | None = None
        self._batch_delete_text = "Select multiple"
        self._delete_selected_text = "Delete selected ({count})"
        self._cancel_batch_text = "Cancel"

        self.feeds_tab = QPushButton()
        self.feeds_tab.setObjectName("PrimarySegment")
        self.feeds_tab.setCheckable(True)
        self.feeds_tab.setChecked(True)

        self.tags_tab = QPushButton()
        self.tags_tab.setObjectName("SecondarySegment")
        self.tags_tab.setCheckable(True)

        self.tab_group = QButtonGroup(self)
        self.tab_group.setExclusive(True)
        self.tab_group.addButton(self.feeds_tab, 0)
        self.tab_group.addButton(self.tags_tab, 1)

        tab_layout = QHBoxLayout()
        tab_layout.setContentsMargins(8, 8, 8, 4)
        tab_layout.setSpacing(6)
        tab_layout.addWidget(self.feeds_tab)
        tab_layout.addWidget(self.tags_tab)

        self.title_label = QLabel()
        self.title_label.setObjectName("PanelTitle")

        self.menu_add_feed_action = QAction(self)
        self.menu_add_feed_action.triggered.connect(self.add_feed_requested)
        self.menu_import_opml_action = QAction(self)
        self.menu_import_opml_action.triggered.connect(
            self.import_opml_requested
        )
        self.menu_refresh_action = QAction(self)
        self.menu_refresh_action.triggered.connect(self.refresh_requested)
        self.menu_batch_delete_action = QAction(self)
        self.menu_batch_delete_action.triggered.connect(
            self._handle_batch_delete_button
        )
        self.menu_delete_feed_action = QAction(self)
        self.menu_delete_feed_action.setEnabled(False)
        self.menu_delete_feed_action.triggered.connect(
            self._request_current_feed_deletion
        )

        self.feed_actions_menu = QMenu(self)
        self.feed_actions_menu.addAction(self.menu_add_feed_action)
        self.feed_actions_menu.addAction(self.menu_import_opml_action)
        self.feed_actions_menu.addSeparator()
        self.feed_actions_menu.addAction(self.menu_refresh_action)
        self.feed_actions_menu.addSeparator()
        self.feed_actions_menu.addAction(self.menu_batch_delete_action)
        self.feed_actions_menu.addAction(self.menu_delete_feed_action)

        self.add_feed_button = QToolButton()
        self.add_feed_button.setObjectName("FeedAddButton")
        self.add_feed_button.setText("+")
        self.add_feed_button.setAutoRaise(True)
        self.add_feed_button.clicked.connect(self.add_feed_requested)

        self.feed_menu_button = QToolButton()
        self.feed_menu_button.setObjectName("FeedMenuButton")
        self.feed_menu_button.setText("▾")
        self.feed_menu_button.setAutoRaise(True)
        self.feed_menu_button.setMenu(self.feed_actions_menu)
        self.feed_menu_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )

        self.batch_delete_button = QPushButton()
        self.batch_delete_button.setObjectName("FeedBatchDeleteButton")
        self.batch_delete_button.clicked.connect(
            self._handle_batch_delete_button
        )

        self.cancel_batch_delete_button = QPushButton()
        self.cancel_batch_delete_button.setObjectName(
            "FeedBatchDeleteCancelButton"
        )
        self.cancel_batch_delete_button.setVisible(False)
        self.cancel_batch_delete_button.clicked.connect(
            self._cancel_batch_delete_mode
        )

        feed_actions_widget = QWidget()
        feed_actions_layout = QHBoxLayout(feed_actions_widget)
        feed_actions_layout.setContentsMargins(0, 0, 0, 0)
        feed_actions_layout.setSpacing(0)
        feed_actions_layout.addWidget(self.add_feed_button)
        feed_actions_layout.addWidget(self.feed_menu_button)

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(12, 4, 12, 2)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch(1)
        title_layout.addWidget(self.batch_delete_button)
        title_layout.addWidget(self.cancel_batch_delete_button)
        title_layout.addWidget(feed_actions_widget)

        self.feed_list = QListWidget()
        self.feed_list.setObjectName("FeedList")
        self.feed_list.setAlternatingRowColors(False)
        self.feed_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.feed_list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.feed_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.feed_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )

        self.footer_label = QLabel()
        self.footer_label.setObjectName("PanelFooter")
        self.footer_label.setWordWrap(True)

        feeds_page = QFrame()
        feeds_page.setObjectName("SidebarPage")
        feeds_layout = QVBoxLayout(feeds_page)
        feeds_layout.setContentsMargins(0, 0, 0, 0)
        feeds_layout.setSpacing(0)
        feeds_layout.addLayout(title_layout)
        feeds_layout.addWidget(self.feed_list, 1)
        feeds_layout.addWidget(self.footer_label)

        self.tag_browser_title = QLabel()
        self.tag_browser_title.setObjectName("PanelTitle")
        self.tag_browser_hint = QLabel()
        self.tag_browser_hint.setObjectName("SidebarHint")
        self.tag_browser_hint.setWordWrap(True)
        self.tag_list = QListWidget()
        self.tag_list.setObjectName("SidebarTagList")
        self.tag_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.tag_list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.tag_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.clear_tag_filter_button = QPushButton()
        self.clear_tag_filter_button.setObjectName("ClearTagFilterButton")
        self.clear_tag_filter_button.clicked.connect(
            self.clear_tag_filter
        )

        tags_page = QFrame()
        tags_page.setObjectName("SidebarPage")
        tags_layout = QVBoxLayout(tags_page)
        tags_layout.setContentsMargins(12, 8, 12, 10)
        tags_layout.setSpacing(7)
        tags_layout.addWidget(self.tag_browser_title)
        tags_layout.addWidget(self.tag_browser_hint)
        tags_layout.addWidget(self.tag_list, 1)
        tags_layout.addWidget(self.clear_tag_filter_button)

        self.pages = QStackedWidget()
        self.pages.setObjectName("SidebarPages")
        self.pages.addWidget(feeds_page)
        self.pages.addWidget(tags_page)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(tab_layout)
        layout.addWidget(self.pages, 1)

        self.feeds_tab.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        self.tags_tab.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        self.feed_list.currentItemChanged.connect(
            self._on_current_item_changed
        )
        self.feed_list.itemSelectionChanged.connect(
            self._on_feed_selection_changed
        )
        self.feed_list.customContextMenuRequested.connect(
            self._show_feed_context_menu
        )
        self.tag_list.itemChanged.connect(
            self._on_tag_check_state_changed
        )
        self.tag_list.customContextMenuRequested.connect(
            self._show_tag_context_menu
        )

    def set_feeds(
        self,
        feeds: list[Feed],
        unread_counts: Mapping[str, int] | None = None,
        starred_count: int = 0,
    ) -> None:
        if self._batch_delete_mode:
            self._set_batch_delete_mode(False, restore_selection=False)
        selected_feed_id = self.current_feed_id() or ALL_FEEDS_ID
        blocker = QSignalBlocker(self.feed_list)
        self.feed_list.clear()
        self.menu_delete_feed_action.setEnabled(False)
        counts = unread_counts or {}
        self._feed_count = len(feeds)
        self._unread_total = sum(max(int(value), 0) for value in counts.values())
        self._starred_total = max(int(starred_count), 0)

        self._add_virtual_feed_item(
            ALL_FEEDS_ID,
            self._all_feeds_text,
            unread_count=self._unread_total,
        )
        self._add_virtual_feed_item(
            STARRED_FEED_ID,
            self._starred_text,
            starred_count=self._starred_total,
        )

        for feed in feeds:
            unread_count = max(int(counts.get(feed.id, 0)), 0)
            item = QListWidgetItem()
            item.setData(FEED_ID_ROLE, feed.id)
            item.setData(FEED_TITLE_ROLE, feed.title)
            item.setData(UNREAD_COUNT_ROLE, unread_count)
            item.setData(IS_VIRTUAL_ROLE, False)
            item.setToolTip(feed.title)
            self._update_feed_item_text(item)
            self.feed_list.addItem(item)

        self.select_feed(selected_feed_id)
        del blocker
        self._update_delete_action_state()
        self._update_footer()

    def update_unread_count(self, feed_id: str, unread_count: int) -> None:
        for index in range(self.feed_list.count()):
            item = self.feed_list.item(index)

            if item.data(FEED_ID_ROLE) != feed_id:
                continue

            item.setData(UNREAD_COUNT_ROLE, max(unread_count, 0))
            self._update_feed_item_text(item)
            self._unread_total = sum(
                int(self.feed_list.item(row).data(UNREAD_COUNT_ROLE) or 0)
                for row in range(self.feed_list.count())
                if not bool(
                    self.feed_list.item(row).data(IS_VIRTUAL_ROLE)
                )
            )
            all_item = self._item_for_feed_id(ALL_FEEDS_ID)
            if all_item is not None:
                all_item.setData(UNREAD_COUNT_ROLE, self._unread_total)
                self._update_feed_item_text(all_item)
            self._update_footer()
            return

    def update_starred_count(self, starred_count: int) -> None:
        self._starred_total = max(int(starred_count), 0)
        item = self._item_for_feed_id(STARRED_FEED_ID)

        if item is None:
            return

        item.setData(STARRED_COUNT_ROLE, self._starred_total)
        self._update_feed_item_text(item)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_tabs(self, feeds_text: str, tags_text: str) -> None:
        self.feeds_tab.setText(feeds_text)
        self.tags_tab.setText(tags_text)

    def set_tag_browser_texts(
        self,
        title: str,
        hint: str,
        *,
        clear_filter: str,
        rename: str,
        delete: str,
    ) -> None:
        self.tag_browser_title.setText(title)
        self.tag_browser_hint.setText(hint)
        self._clear_tag_filter_text = clear_filter
        self._rename_tag_text = rename
        self._delete_tag_text = delete
        self.clear_tag_filter_button.setText(clear_filter)

    def set_tags(
        self,
        tags: list[Tag],
        selected_tag_ids: Collection[str] = (),
    ) -> None:
        selected_ids = {str(tag_id) for tag_id in selected_tag_ids}
        blocker = QSignalBlocker(self.tag_list)
        self.tag_list.clear()
        for tag in tags:
            item = QListWidgetItem(
                f"{tag.name}  \N{MIDDLE DOT}  {tag.article_count}"
            )
            item.setData(TAG_ID_ROLE, tag.id)
            item.setData(TAG_NAME_ROLE, tag.name)
            item.setData(TAG_COUNT_ROLE, tag.article_count)
            item.setToolTip(tag.name)
            item.setFlags(
                item.flags() | Qt.ItemFlag.ItemIsUserCheckable
            )
            item.setCheckState(
                Qt.CheckState.Checked
                if tag.id in selected_ids
                else Qt.CheckState.Unchecked
            )
            self.tag_list.addItem(item)
        del blocker
        self.clear_tag_filter_button.setEnabled(
            bool(self.selected_tag_ids())
        )

    def selected_tag_ids(self) -> tuple[str, ...]:
        return tuple(
            str(item.data(TAG_ID_ROLE))
            for row in range(self.tag_list.count())
            if (item := self.tag_list.item(row)).checkState()
            == Qt.CheckState.Checked
        )

    def clear_tag_filter(self) -> None:
        blocker = QSignalBlocker(self.tag_list)
        for row in range(self.tag_list.count()):
            self.tag_list.item(row).setCheckState(
                Qt.CheckState.Unchecked
            )
        del blocker
        self.clear_tag_filter_button.setEnabled(False)
        self.tag_filter_changed.emit(())

    def _on_tag_check_state_changed(self, _item) -> None:
        selected_ids = self.selected_tag_ids()
        self.clear_tag_filter_button.setEnabled(bool(selected_ids))
        self.tag_filter_changed.emit(selected_ids)

    def set_action_texts(
        self,
        *,
        add_feed: str,
        import_opml: str,
        refresh: str,
        delete_feed: str,
        batch_delete: str = "Select multiple",
        delete_selected: str = "Delete selected ({count})",
        cancel_selection: str = "Cancel",
    ) -> None:
        self.add_feed_button.setToolTip(add_feed)
        self.add_feed_button.setAccessibleName(add_feed)
        self.feed_menu_button.setToolTip(import_opml)
        self.feed_menu_button.setAccessibleName(import_opml)
        self.menu_add_feed_action.setText(add_feed)
        self.menu_import_opml_action.setText(import_opml)
        self.menu_refresh_action.setText(refresh)
        self.menu_batch_delete_action.setText(batch_delete)
        self.menu_delete_feed_action.setText(delete_feed)
        self._batch_delete_text = batch_delete
        self._delete_selected_text = delete_selected
        self._cancel_batch_text = cancel_selection
        self._update_batch_delete_controls()

    def set_footer(self, footer_text: str) -> None:
        self._footer_template = footer_text
        self._update_footer()

    def set_feed_detail_text(self, detail_text: str) -> None:
        self._feed_detail_text = detail_text

        for index in range(self.feed_list.count()):
            self._update_feed_item_text(self.feed_list.item(index))

    def set_virtual_feed_texts(
        self,
        *,
        all_feeds: str,
        starred: str,
        starred_detail: str,
    ) -> None:
        self._all_feeds_text = all_feeds
        self._starred_text = starred
        self._starred_detail_text = starred_detail

        all_item = self._item_for_feed_id(ALL_FEEDS_ID)
        if all_item is not None:
            all_item.setData(FEED_TITLE_ROLE, all_feeds)
            all_item.setToolTip(all_feeds)
            self._update_feed_item_text(all_item)

        starred_item = self._item_for_feed_id(STARRED_FEED_ID)
        if starred_item is not None:
            starred_item.setData(FEED_TITLE_ROLE, starred)
            starred_item.setToolTip(starred)
            self._update_feed_item_text(starred_item)

    def current_feed_id(self) -> str | None:
        item = self.feed_list.currentItem()
        if item is None:
            return None
        return str(item.data(FEED_ID_ROLE))

    def selected_feed_ids(self) -> tuple[str, ...]:
        return tuple(
            str(item.data(FEED_ID_ROLE))
            for item in self.feed_list.selectedItems()
            if not bool(item.data(IS_VIRTUAL_ROLE))
        )

    def select_feed(self, feed_id: str) -> bool:
        item = self._item_for_feed_id(feed_id)
        if item is None:
            item = self._item_for_feed_id(ALL_FEEDS_ID)
        if item is None:
            return False

        self.feed_list.clearSelection()
        self.feed_list.setCurrentItem(item)
        return True

    def _on_current_item_changed(self, current, previous) -> None:
        del previous

        self._update_delete_action_state()

        if current is None:
            return
        if self._batch_delete_mode:
            return

        feed_id = current.data(FEED_ID_ROLE)
        self.feed_selected.emit(feed_id)

    def _request_current_feed_deletion(self) -> None:
        current = self.feed_list.currentItem()
        if current is None or bool(current.data(IS_VIRTUAL_ROLE)):
            return
        self._emit_feed_deletion_request(
            (str(current.data(FEED_ID_ROLE)),)
        )

    def _handle_batch_delete_button(self) -> None:
        if not self._batch_delete_mode:
            self._set_batch_delete_mode(True)
            return
        self._emit_feed_deletion_request(self.selected_feed_ids())

    def _cancel_batch_delete_mode(self) -> None:
        self._set_batch_delete_mode(False)

    def _set_batch_delete_mode(
        self,
        enabled: bool,
        *,
        restore_selection: bool = True,
    ) -> None:
        if enabled == self._batch_delete_mode:
            return

        if enabled:
            self._feed_id_before_batch = self.current_feed_id()
            self._batch_delete_mode = True
            self.feed_list.setSelectionMode(
                QAbstractItemView.SelectionMode.MultiSelection
            )
            self.feed_list.clearSelection()
        else:
            previous_feed_id = self._feed_id_before_batch
            self._batch_delete_mode = False
            self._feed_id_before_batch = None
            self.feed_list.setSelectionMode(
                QAbstractItemView.SelectionMode.SingleSelection
            )
            self.feed_list.clearSelection()
            if restore_selection and previous_feed_id is not None:
                self.select_feed(previous_feed_id)

        self._update_delete_action_state()

    def _on_feed_selection_changed(self) -> None:
        if self._batch_delete_mode:
            blocker = QSignalBlocker(self.feed_list)
            for item in self.feed_list.selectedItems():
                if bool(item.data(IS_VIRTUAL_ROLE)):
                    item.setSelected(False)
            del blocker
        self._update_delete_action_state()

    def _update_delete_action_state(self) -> None:
        current = self.feed_list.currentItem()
        self.menu_delete_feed_action.setEnabled(
            not self._batch_delete_mode
            and current is not None
            and not bool(current.data(IS_VIRTUAL_ROLE))
        )
        self._update_batch_delete_controls()

    def _update_batch_delete_controls(self) -> None:
        selected_count = len(self.selected_feed_ids())
        self.cancel_batch_delete_button.setText(self._cancel_batch_text)
        self.cancel_batch_delete_button.setVisible(
            self._batch_delete_mode
        )
        self.add_feed_button.setVisible(not self._batch_delete_mode)
        self.feed_menu_button.setVisible(not self._batch_delete_mode)
        self.menu_batch_delete_action.setEnabled(
            not self._batch_delete_mode and self._feed_count > 0
        )
        if self._batch_delete_mode:
            self.batch_delete_button.setVisible(True)
            self.batch_delete_button.setText(
                self._delete_selected_text.format(count=selected_count)
            )
            self.batch_delete_button.setEnabled(selected_count > 0)
            return

        self.batch_delete_button.setText(self._batch_delete_text)
        self.batch_delete_button.setEnabled(self._feed_count > 0)
        self.batch_delete_button.setVisible(False)

    def _emit_feed_deletion_request(
        self,
        feed_ids: Collection[str],
    ) -> None:
        normalized_ids = tuple(
            dict.fromkeys(str(feed_id) for feed_id in feed_ids)
        )
        if not normalized_ids:
            return

        if len(normalized_ids) == 1:
            self.delete_feed_requested.emit(normalized_ids[0])
        self.delete_feeds_requested.emit(normalized_ids)

    def _show_feed_context_menu(self, position) -> None:
        item = self.feed_list.itemAt(position)

        if item is None:
            return
        if bool(item.data(IS_VIRTUAL_ROLE)):
            return

        menu = self._build_feed_context_menu(item)
        menu.exec(self.feed_list.viewport().mapToGlobal(position))

    def _build_feed_context_menu(self, item: QListWidgetItem) -> QMenu:
        if bool(item.data(IS_VIRTUAL_ROLE)):
            return QMenu(self)

        feed_id = str(item.data(FEED_ID_ROLE))
        selected_feed_ids = self.selected_feed_ids()
        deletion_targets = (
            selected_feed_ids
            if item.isSelected() and feed_id in selected_feed_ids
            else (feed_id,)
        )
        menu = QMenu(self)
        delete_action = menu.addAction(
            self.menu_delete_feed_action.text()
        )
        delete_action.setObjectName("ContextDeleteFeedAction")
        delete_action.triggered.connect(
            lambda checked=False: self._emit_feed_deletion_request(
                deletion_targets
            )
        )
        return menu

    def _show_tag_context_menu(self, position) -> None:
        item = self.tag_list.itemAt(position)
        if item is None:
            return

        tag_id = str(item.data(TAG_ID_ROLE))
        menu = QMenu(self)
        rename_action = menu.addAction(self._rename_tag_text)
        rename_action.setObjectName("ContextRenameTagAction")
        rename_action.triggered.connect(
            lambda checked=False: self.rename_tag_requested.emit(tag_id)
        )
        delete_action = menu.addAction(self._delete_tag_text)
        delete_action.setObjectName("ContextDeleteTagAction")
        delete_action.triggered.connect(
            lambda checked=False: self.delete_tag_requested.emit(tag_id)
        )
        menu.exec(self.tag_list.viewport().mapToGlobal(position))

    def _update_feed_item_text(self, item: QListWidgetItem) -> None:
        title = str(item.data(FEED_TITLE_ROLE) or "")
        if item.data(FEED_ID_ROLE) == STARRED_FEED_ID:
            starred_count = int(item.data(STARRED_COUNT_ROLE) or 0)
            detail = self._starred_detail_text.format(
                count=starred_count
            )
            item.setText(f"{title}  ·  {detail}")
            return

        unread_count = int(item.data(UNREAD_COUNT_ROLE) or 0)
        detail = self._feed_detail_text.format(count=unread_count)
        item.setText(f"{title}  ·  {detail}")

    def _add_virtual_feed_item(
        self,
        feed_id: str,
        title: str,
        *,
        unread_count: int = 0,
        starred_count: int = 0,
    ) -> None:
        item = QListWidgetItem()
        item.setData(FEED_ID_ROLE, feed_id)
        item.setData(FEED_TITLE_ROLE, title)
        item.setData(UNREAD_COUNT_ROLE, unread_count)
        item.setData(STARRED_COUNT_ROLE, starred_count)
        item.setData(IS_VIRTUAL_ROLE, True)
        item.setToolTip(title)

        if feed_id == STARRED_FEED_ID:
            item.setIcon(self._starred_icon())

        self._update_feed_item_text(item)
        self.feed_list.addItem(item)

    def _item_for_feed_id(
        self,
        feed_id: str,
    ) -> QListWidgetItem | None:
        for row in range(self.feed_list.count()):
            item = self.feed_list.item(row)
            if str(item.data(FEED_ID_ROLE)) == str(feed_id):
                return item
        return None

    @staticmethod
    def _starred_icon() -> QIcon:
        pixmap = QPixmap(18, 18)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        draw_star(
            painter,
            QRectF(2, 2, 14, 14),
            filled=True,
            color=QColor("#f4c542"),
        )
        painter.end()
        return QIcon(pixmap)

    def _update_footer(self) -> None:
        self.footer_label.setText(
            self._footer_template.format(
                feeds=self._feed_count,
                unread=self._unread_total,
            )
        )
