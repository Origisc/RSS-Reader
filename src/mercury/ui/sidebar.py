from collections.abc import Mapping

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
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


FEED_ID_ROLE = Qt.ItemDataRole.UserRole
FEED_TITLE_ROLE = Qt.ItemDataRole.UserRole + 1
UNREAD_COUNT_ROLE = Qt.ItemDataRole.UserRole + 2


class Sidebar(QWidget):
    """左侧订阅源区域。"""

    feed_selected = Signal(str)
    add_feed_requested = Signal()
    import_opml_requested = Signal()
    refresh_requested = Signal()
    delete_feed_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("SidebarPanel")
        self._feed_detail_text = "{count} unread"
        self._footer_template = "Feeds: {feeds} · Unread: {unread}"
        self._feed_count = 0
        self._unread_total = 0

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
        self.feed_actions_menu.addAction(self.menu_delete_feed_action)

        self.add_feed_button = QToolButton()
        self.add_feed_button.setObjectName("FeedAddButton")
        self.add_feed_button.setText("+")
        self.add_feed_button.setAutoRaise(True)
        self.add_feed_button.clicked.connect(self.add_feed_requested)

        self.feed_menu_button = QToolButton()
        self.feed_menu_button.setObjectName("FeedMenuButton")
        self.feed_menu_button.setArrowType(Qt.ArrowType.DownArrow)
        self.feed_menu_button.setAutoRaise(True)
        self.feed_menu_button.setMenu(self.feed_actions_menu)
        self.feed_menu_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
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
        title_layout.addWidget(feed_actions_widget)

        self.feed_list = QListWidget()
        self.feed_list.setObjectName("FeedList")
        self.feed_list.setAlternatingRowColors(False)
        self.feed_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.feed_list.setTextElideMode(Qt.TextElideMode.ElideRight)
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

        tags_page = QFrame()
        tags_page.setObjectName("SidebarPage")
        tags_layout = QVBoxLayout(tags_page)
        tags_layout.setContentsMargins(12, 8, 12, 10)
        tags_layout.setSpacing(7)
        tags_layout.addWidget(self.tag_browser_title)
        tags_layout.addWidget(self.tag_browser_hint)
        tags_layout.addWidget(self.tag_list, 1)

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
        self.feed_list.customContextMenuRequested.connect(
            self._show_feed_context_menu
        )

    def set_feeds(
        self,
        feeds: list[Feed],
        unread_counts: Mapping[str, int] | None = None,
    ) -> None:
        self.feed_list.clear()
        self.menu_delete_feed_action.setEnabled(False)
        counts = unread_counts or {}
        self._feed_count = len(feeds)
        self._unread_total = sum(max(int(value), 0) for value in counts.values())

        for feed in feeds:
            unread_count = max(int(counts.get(feed.id, 0)), 0)
            item = QListWidgetItem()
            item.setData(FEED_ID_ROLE, feed.id)
            item.setData(FEED_TITLE_ROLE, feed.title)
            item.setData(UNREAD_COUNT_ROLE, unread_count)
            item.setToolTip(feed.title)
            self._update_feed_item_text(item)
            self.feed_list.addItem(item)

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
            )
            self._update_footer()
            return

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_tabs(self, feeds_text: str, tags_text: str) -> None:
        self.feeds_tab.setText(feeds_text)
        self.tags_tab.setText(tags_text)

    def set_tag_browser_texts(self, title: str, hint: str) -> None:
        self.tag_browser_title.setText(title)
        self.tag_browser_hint.setText(hint)

    def set_tags(self, tags: list[str]) -> None:
        self.tag_list.clear()
        self.tag_list.addItems(tags)

    def set_action_texts(
        self,
        *,
        add_feed: str,
        import_opml: str,
        refresh: str,
        delete_feed: str,
    ) -> None:
        self.add_feed_button.setToolTip(add_feed)
        self.add_feed_button.setAccessibleName(add_feed)
        self.feed_menu_button.setToolTip(import_opml)
        self.feed_menu_button.setAccessibleName(import_opml)
        self.menu_add_feed_action.setText(add_feed)
        self.menu_import_opml_action.setText(import_opml)
        self.menu_refresh_action.setText(refresh)
        self.menu_delete_feed_action.setText(delete_feed)

    def set_footer(self, footer_text: str) -> None:
        self._footer_template = footer_text
        self._update_footer()

    def set_feed_detail_text(self, detail_text: str) -> None:
        self._feed_detail_text = detail_text

        for index in range(self.feed_list.count()):
            self._update_feed_item_text(self.feed_list.item(index))

    def _on_current_item_changed(self, current, previous) -> None:
        del previous

        self.menu_delete_feed_action.setEnabled(current is not None)

        if current is None:
            return

        feed_id = current.data(FEED_ID_ROLE)
        self.feed_selected.emit(feed_id)

    def _request_current_feed_deletion(self) -> None:
        current = self.feed_list.currentItem()

        if current is None:
            return

        self.delete_feed_requested.emit(str(current.data(FEED_ID_ROLE)))

    def _show_feed_context_menu(self, position) -> None:
        item = self.feed_list.itemAt(position)

        if item is None:
            return

        menu = self._build_feed_context_menu(item)
        menu.exec(self.feed_list.viewport().mapToGlobal(position))

    def _build_feed_context_menu(self, item: QListWidgetItem) -> QMenu:
        feed_id = str(item.data(FEED_ID_ROLE))
        menu = QMenu(self)
        delete_action = menu.addAction(
            self.menu_delete_feed_action.text()
        )
        delete_action.setObjectName("ContextDeleteFeedAction")
        delete_action.triggered.connect(
            lambda checked=False: self.delete_feed_requested.emit(feed_id)
        )
        return menu

    def _update_feed_item_text(self, item: QListWidgetItem) -> None:
        title = str(item.data(FEED_TITLE_ROLE) or "")
        unread_count = int(item.data(UNREAD_COUNT_ROLE) or 0)
        detail = self._feed_detail_text.format(count=unread_count)
        item.setText(f"{title}  ·  {detail}")

    def _update_footer(self) -> None:
        self.footer_label.setText(
            self._footer_template.format(
                feeds=self._feed_count,
                unread=self._unread_total,
            )
        )
