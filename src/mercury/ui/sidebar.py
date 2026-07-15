from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QListWidget, QVBoxLayout, QWidget

from mercury.models.article import Feed


class Sidebar(QWidget):
    """左侧订阅源区域。"""

    feed_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self.title_label = QLabel()
        self.feed_list = QListWidget()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.title_label)
        layout.addWidget(self.feed_list)

        self.feed_list.currentItemChanged.connect(
            self._on_current_item_changed
        )

    def set_feeds(self, feeds: list[Feed]) -> None:
        self.feed_list.clear()

        for feed in feeds:
            self.feed_list.addItem(feed.title)
            item = self.feed_list.item(self.feed_list.count() - 1)
            item.setData(256, feed.id)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def _on_current_item_changed(self, current, previous) -> None:
        del previous

        if current is None:
            return

        feed_id = current.data(256)
        self.feed_selected.emit(feed_id)