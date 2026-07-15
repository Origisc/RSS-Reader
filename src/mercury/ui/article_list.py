from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QListWidget, QVBoxLayout, QWidget

from mercury.models.article import Article


class ArticleList(QWidget):
    """中间文章列表区域。"""

    article_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self.list_widget = QListWidget()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("文章列表"))
        layout.addWidget(self.list_widget)

        self.list_widget.currentItemChanged.connect(
            self._on_current_item_changed
        )

    def set_articles(self, articles: list[Article]) -> None:
        self.list_widget.clear()

        for article in articles:
            self.list_widget.addItem(article.title)
            item = self.list_widget.item(self.list_widget.count() - 1)
            item.setData(256, article.id)

    def _on_current_item_changed(self, current, previous) -> None:
        del previous

        if current is None:
            return

        article_id = current.data(256)
        self.article_selected.emit(article_id)