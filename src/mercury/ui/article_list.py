from collections.abc import Collection
from dataclasses import replace

from PySide6.QtCore import (
    QEvent,
    QRect,
    QRectF,
    QSignalBlocker,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QFontMetrics, QMouseEvent, QPainter
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from mercury.models.article import Article
from mercury.ui.star_icon import draw_star


ARTICLE_ID_ROLE = Qt.ItemDataRole.UserRole
READ_STATE_ROLE = Qt.ItemDataRole.UserRole + 1
ARTICLE_TITLE_ROLE = Qt.ItemDataRole.UserRole + 2
ARTICLE_SOURCE_ROLE = Qt.ItemDataRole.UserRole + 3
STARRED_STATE_ROLE = Qt.ItemDataRole.UserRole + 4


class WrappingArticleDelegate(QStyledItemDelegate):
    """Measure entry text against the current viewport width."""

    star_toggled = Signal(str, bool)

    def __init__(self, article_list: QListWidget) -> None:
        super().__init__(article_list)
        self._article_list = article_list
        self._star_text = "Star"
        self._unstar_text = "Unstar"

    def sizeHint(
        self,
        option: QStyleOptionViewItem,
        index,
    ) -> QSize:
        wrapped_option = QStyleOptionViewItem(option)
        self.initStyleOption(wrapped_option, index)

        horizontal_padding = 60
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

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index,
    ) -> None:
        content_option = QStyleOptionViewItem(option)
        content_option.rect = content_option.rect.adjusted(0, 0, -36, 0)
        super().paint(painter, content_option, index)

        is_starred = bool(index.data(STARRED_STATE_ROLE))
        is_hovered = bool(
            option.state & QStyle.StateFlag.State_MouseOver
        )
        is_selected = bool(
            option.state & QStyle.StateFlag.State_Selected
        )

        if not (is_starred or is_hovered or is_selected):
            return

        painter.save()
        star_rect = self._star_rect(option)
        icon_size = 15.0
        draw_star(
            painter,
            QRectF(
                star_rect.center().x() - icon_size / 2,
                star_rect.center().y() - icon_size / 2,
                icon_size,
                icon_size,
            ),
            filled=is_starred,
            color=(
                QColor("#f4c542")
                if is_starred
                else QColor("#8a949e")
            ),
        )
        painter.restore()

    def editorEvent(
        self,
        event: QEvent,
        model,
        option: QStyleOptionViewItem,
        index,
    ) -> bool:
        if (
            isinstance(event, QMouseEvent)
            and event.button() == Qt.MouseButton.LeftButton
            and self._star_rect(option).contains(
                event.position().toPoint()
            )
        ):
            if event.type() == QEvent.Type.MouseButtonRelease:
                article_id = str(index.data(ARTICLE_ID_ROLE))
                self.star_toggled.emit(
                    article_id,
                    not bool(index.data(STARRED_STATE_ROLE)),
                )
            return True

        return super().editorEvent(event, model, option, index)

    def helpEvent(self, event, view, option, index) -> bool:
        if self._star_rect(option).contains(event.pos()):
            text = (
                self._unstar_text
                if bool(index.data(STARRED_STATE_ROLE))
                else self._star_text
            )
            QToolTip.showText(event.globalPos(), text, view)
            return True

        return super().helpEvent(event, view, option, index)

    def set_star_texts(self, star: str, unstar: str) -> None:
        self._star_text = star
        self._unstar_text = unstar

    @staticmethod
    def _star_rect(option: QStyleOptionViewItem) -> QRect:
        return QRect(
            option.rect.right() - 35,
            option.rect.top(),
            36,
            option.rect.height(),
        )


class ArticleList(QWidget):
    """中间文章列表区域。"""

    article_selected = Signal(str)
    star_toggled = Signal(str, bool)

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("ArticleListPanel")
        self._entry_meta_text = "Mock entry"
        self._color_scheme = "dark"
        self._articles: list[Article] = []
        self._read_article_ids: set[str] = set()

        self.title_label = QLabel()
        self.title_label.setObjectName("PanelTitle")

        self.unread_filter_button = QPushButton()
        self.unread_filter_button.setObjectName("EntryFilterButton")
        self.unread_filter_button.setCheckable(True)
        self.unread_filter_button.toggled.connect(
            lambda _checked: self._render_articles()
        )

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(12, 7, 10, 6)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.unread_filter_button)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("EntryList")
        self.list_widget.setWordWrap(True)
        self.list_widget.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.list_widget.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.list_widget.setUniformItemSizes(False)
        self.list_widget.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_widget.setMouseTracking(True)
        self._delegate = WrappingArticleDelegate(self.list_widget)
        self._delegate.star_toggled.connect(self.star_toggled.emit)
        self.list_widget.setItemDelegate(self._delegate)

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
        self._articles = list(articles)
        self._read_article_ids = set(read_article_ids or set())
        self._render_articles()

    def _render_articles(self) -> None:
        self.list_widget.clear()

        for article in self._articles:
            is_read = article.id in self._read_article_ids
            if self.unread_filter_button.isChecked() and is_read:
                continue

            item = QListWidgetItem()
            item.setData(ARTICLE_ID_ROLE, article.id)
            item.setData(READ_STATE_ROLE, is_read)
            item.setData(ARTICLE_TITLE_ROLE, article.title)
            item.setData(ARTICLE_SOURCE_ROLE, article.source_title)
            item.setData(STARRED_STATE_ROLE, article.is_starred)
            item.setToolTip(article.title)
            self._update_item_text(item)
            self._apply_read_style(item)
            self.list_widget.addItem(item)

        self.list_widget.doItemsLayout()

    def set_read_state(self, article_id: str, is_read: bool) -> None:
        if is_read:
            self._read_article_ids.add(article_id)
        else:
            self._read_article_ids.discard(article_id)

        if self.unread_filter_button.isChecked():
            self._render_articles()
            return

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

        self.list_widget.viewport().update()

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_filter_text(self, unread: str) -> None:
        self.unread_filter_button.setText(unread)

    def set_entry_meta_text(self, text: str) -> None:
        self._entry_meta_text = text

        for index in range(self.list_widget.count()):
            self._update_item_text(self.list_widget.item(index))

        self.list_widget.doItemsLayout()

    def set_star_texts(self, *, star: str, unstar: str) -> None:
        self._delegate.set_star_texts(star, unstar)

    def set_starred_state(
        self,
        article_id: str,
        is_starred: bool,
    ) -> None:
        self._articles = [
            (
                replace(article, is_starred=is_starred)
                if article.id == article_id
                else article
            )
            for article in self._articles
        ]

        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if str(item.data(ARTICLE_ID_ROLE)) != article_id:
                continue

            item.setData(STARRED_STATE_ROLE, is_starred)
            self.list_widget.viewport().update(
                self.list_widget.visualItemRect(item)
            )
            return

    def remove_article(self, article_id: str) -> None:
        selected_id = self.current_article_id()
        self._articles = [
            article
            for article in self._articles
            if article.id != article_id
        ]
        blocker = QSignalBlocker(self.list_widget)

        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if str(item.data(ARTICLE_ID_ROLE)) == article_id:
                self.list_widget.takeItem(row)
                break

        if selected_id == article_id:
            self.list_widget.setCurrentItem(None)
            self.list_widget.clearSelection()
        elif selected_id is not None:
            self.select_article(selected_id)

        del blocker

    def visible_article_ids(self) -> list[str]:
        return [
            str(self.list_widget.item(row).data(ARTICLE_ID_ROLE))
            for row in range(self.list_widget.count())
        ]

    def current_article_id(self) -> str | None:
        item = self.list_widget.currentItem()
        if item is None:
            return None
        return str(item.data(ARTICLE_ID_ROLE))

    def select_article(self, article_id: str) -> bool:
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if str(item.data(ARTICLE_ID_ROLE)) != article_id:
                continue

            self.list_widget.setCurrentItem(item)
            return True

        return False

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
