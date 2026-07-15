from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from mercury.models.article import Feed


class Sidebar(QWidget):
    """左侧订阅源区域。"""

    feed_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("SidebarPanel")
        self._feed_detail_text = "{count} unread"

        self.feeds_tab = QPushButton()
        self.feeds_tab.setObjectName("PrimarySegment")
        self.feeds_tab.setCheckable(True)
        self.feeds_tab.setChecked(True)

        self.tags_tab = QPushButton()
        self.tags_tab.setObjectName("SecondarySegment")
        self.tags_tab.setCheckable(True)
        self.tags_tab.setEnabled(False)

        tab_layout = QHBoxLayout()
        tab_layout.setContentsMargins(8, 8, 8, 4)
        tab_layout.setSpacing(6)
        tab_layout.addWidget(self.feeds_tab)
        tab_layout.addWidget(self.tags_tab)

        self.title_label = QLabel()
        self.title_label.setObjectName("PanelTitle")
        self.add_label = QLabel("+  ⌄")
        self.add_label.setObjectName("PanelActionHint")

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(12, 4, 12, 2)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch(1)
        title_layout.addWidget(self.add_label)

        self.feed_list = QListWidget()
        self.feed_list.setObjectName("FeedList")
        self.feed_list.setAlternatingRowColors(False)

        self.footer_label = QLabel()
        self.footer_label.setObjectName("PanelFooter")
        self.footer_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(tab_layout)
        layout.addLayout(title_layout)
        layout.addWidget(self.feed_list, 1)
        layout.addWidget(self.footer_label)

        self.feed_list.currentItemChanged.connect(
            self._on_current_item_changed
        )

    def set_feeds(self, feeds: list[Feed]) -> None:
        self.feed_list.clear()

        for index, feed in enumerate(feeds, start=1):
            item = QListWidgetItem(
                f"{feed.title}\n  {self._feed_detail_text.format(count=index)}"
            )
            item.setData(256, feed.id)
            item.setToolTip(feed.title)
            self.feed_list.addItem(item)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_tabs(self, feeds_text: str, tags_text: str) -> None:
        self.feeds_tab.setText(feeds_text)
        self.tags_tab.setText(tags_text)

    def set_footer(self, footer_text: str) -> None:
        self.footer_label.setText(footer_text)

    def set_feed_detail_text(self, detail_text: str) -> None:
        self._feed_detail_text = detail_text

    def _on_current_item_changed(self, current, previous) -> None:
        del previous

        if current is None:
            return

        feed_id = current.data(256)
        self.feed_selected.emit(feed_id)