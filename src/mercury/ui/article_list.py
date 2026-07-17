from collections.abc import Collection

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from mercury.models.article import Article


ARTICLE_ID_ROLE = Qt.ItemDataRole.UserRole
READ_STATE_ROLE = Qt.ItemDataRole.UserRole + 1
ARTICLE_TITLE_ROLE = Qt.ItemDataRole.UserRole + 2
ARTICLE_SOURCE_ROLE = Qt.ItemDataRole.UserRole + 3


class WrappingArticleDelegate(QStyledItemDelegate):
    """Measure entry text against the current viewport width."""

    def __init__(self, article_list: QListWidget) -> None:
        super().__init__(article_list)
        self._article_list = article_list

    def sizeHint(
        self,
        option: QStyleOptionViewItem,
        index,
    ) -> QSize:
        wrapped_option = QStyleOptionViewItem(option)
        self.initStyleOption(wrapped_option, index)

        horizontal_padding = 24
        available_width = max(
            self._article_list.viewport().width() - horizontal_padding,
            80,
        )
        text_flags = int(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignTop
            | Qt.TextFlag.TextWordWrap
        )
        text_bounds = QFontMetrics(wrapped_option.font).boundingRect(
            QRect(0, 0, available_width, 100_000),
            text_flags,
            wrapped_option.text,
        )
        default_size = super().sizeHint(wrapped_option, index)

        return QSize(
            available_width + horizontal_padding,
            max(default_size.height(), text_bounds.height() + 16),
        )


class ArticleList(QWidget):
    """中间文章列表区域。"""

    article_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("ArticleListPanel")
        self._entry_meta_text = "Mock entry"
        self._color_scheme = "dark"

        self.title_label = QLabel()
        self.title_label.setObjectName("PanelTitle")

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(12, 10, 12, 6)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("EntryList")
        self.list_widget.setWordWrap(True)
        self.list_widget.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.list_widget.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.list_widget.setUniformItemSizes(False)
        self.list_widget.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_widget.setItemDelegate(
            WrappingArticleDelegate(self.list_widget)
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(header_layout)
        layout.addWidget(self.list_widget)

        self.list_widget.currentItemChanged.connect(
            self._on_current_item_changed
        )

    def set_articles(
        self,
        articles: list[Article],
        read_article_ids: Collection[str] | None = None,
    ) -> None:
        self.list_widget.clear()
        read_ids = set(read_article_ids or set())

        for article in articles:
            item = QListWidgetItem()
            item.setData(ARTICLE_ID_ROLE, article.id)
            item.setData(READ_STATE_ROLE, article.id in read_ids)
            item.setData(ARTICLE_TITLE_ROLE, article.title)
            item.setData(ARTICLE_SOURCE_ROLE, article.source_title)
            item.setToolTip(article.title)
            self._update_item_text(item)
            self._apply_read_style(item)
            self.list_widget.addItem(item)

        self.list_widget.doItemsLayout()

    def set_read_state(self, article_id: str, is_read: bool) -> None:
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)

            if item.data(ARTICLE_ID_ROLE) != article_id:
                continue

            item.setData(READ_STATE_ROLE, is_read)
            self._apply_read_style(item)
            self.list_widget.doItemsLayout()
            return

    def set_color_scheme(self, theme: str) -> None:
        self._color_scheme = "light" if theme == "light" else "dark"

        for index in range(self.list_widget.count()):
            self._apply_read_style(self.list_widget.item(index))

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_entry_meta_text(self, text: str) -> None:
        self._entry_meta_text = text

        for index in range(self.list_widget.count()):
            self._update_item_text(self.list_widget.item(index))

        self.list_widget.doItemsLayout()

    def _on_current_item_changed(self, current, previous) -> None:
        del previous

        if current is None:
            return

        article_id = current.data(ARTICLE_ID_ROLE)
        self.article_selected.emit(article_id)

    def _apply_read_style(self, item: QListWidgetItem) -> None:
        is_read = bool(item.data(READ_STATE_ROLE))
        font = item.font()
        font.setBold(not is_read)
        item.setFont(font)

        if self._color_scheme == "light":
            color = "#8a949e" if is_read else "#1f2933"
        else:
            color = "#778391" if is_read else "#e5edf5"

        item.setForeground(QColor(color))

    def _update_item_text(self, item: QListWidgetItem) -> None:
        title = item.data(ARTICLE_TITLE_ROLE) or ""
        source_title = item.data(ARTICLE_SOURCE_ROLE) or ""
        item.setText(
            f"• {title}\n{source_title}\n{self._entry_meta_text}"
        )
