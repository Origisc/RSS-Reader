from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Signal

from mercury.models.article import Article


class ArticleList(QWidget):
    """中间文章列表区域。"""

    article_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("ArticleListPanel")
        self._entry_meta_text = "Mock entry"

        self.title_label = QLabel()
        self.title_label.setObjectName("PanelTitle")
        self.filter_button = QPushButton()
        self.filter_button.setObjectName("CompactFilterButton")
        self.filter_button.setEnabled(False)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(12, 10, 12, 6)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.filter_button)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("EntryList")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(header_layout)
        layout.addWidget(self.list_widget)

        self.list_widget.currentItemChanged.connect(
            self._on_current_item_changed
        )

    def set_articles(self, articles: list[Article]) -> None:
        self.list_widget.clear()

        for article in articles:
            item = QListWidgetItem(
                f"• {article.title}\n{article.source_title}\n{self._entry_meta_text}"
            )
            item.setData(256, article.id)
            item.setToolTip(article.title)
            self.list_widget.addItem(item)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_filter_text(self, text: str) -> None:
        self.filter_button.setText(text)

    def set_entry_meta_text(self, text: str) -> None:
        self._entry_meta_text = text

    def _on_current_item_changed(self, current, previous) -> None:
        del previous

        if current is None:
            return

        article_id = current.data(256)
        self.article_selected.emit(article_id)