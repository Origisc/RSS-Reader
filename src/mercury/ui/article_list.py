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
    QMenu,
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
ARTICLE_META_ROLE = Qt.ItemDataRole.UserRole + 5


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
        title = str(index.data(ARTICLE_TITLE_ROLE) or "")
        title_font = option.font
        title_font.setBold(not bool(index.data(READ_STATE_ROLE)))
        horizontal_padding = 76
        available_width = max(
            self._article_list.viewport().width() - horizontal_padding,
            80,
        )
        text_flags = int(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignTop
            | Qt.TextFlag.TextWordWrap
        )
        text_bounds = QFontMetrics(title_font).boundingRect(
            QRect(0, 0, available_width, 100_000),
            text_flags,
            title,
        )
        metadata_height = QFontMetrics(option.font).height() * 2 + 14

        return QSize(
            available_width + horizontal_padding,
            max(72, text_bounds.height() + metadata_height + 16),
        )

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index,
    ) -> None:
        is_starred = bool(index.data(STARRED_STATE_ROLE))
        is_read = bool(index.data(READ_STATE_ROLE))
        is_hovered = bool(
            option.state & QStyle.StateFlag.State_MouseOver
        )
        is_selected = bool(
            option.state & QStyle.StateFlag.State_Selected
        )

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        scheme = str(
            self._article_list.property("colorScheme") or "dark"
        )
        row_rect = option.rect.adjusted(6, 3, -6, -3)

        if is_selected:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(
                QColor("#0b6fe8" if scheme == "dark" else "#dbeafe")
            )
            painter.drawRoundedRect(QRectF(row_rect), 8, 8)
        elif is_hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(
                QColor("#2a2f35" if scheme == "dark" else "#eef1f4")
            )
            painter.drawRoundedRect(QRectF(row_rect), 8, 8)

        if is_selected and scheme == "dark":
            title_color = QColor("#ffffff")
            meta_color = QColor("#d7e6fa")
        elif is_selected:
            title_color = QColor("#17324d")
            meta_color = QColor("#486581")
        else:
            title_color = QColor(
                "#7f8790"
                if is_read
                else ("#f1f3f5" if scheme == "dark" else "#202124")
            )
            meta_color = QColor(
                "#9aa1a9" if scheme == "dark" else "#737980"
            )

        content_left = row_rect.left() + 22
        content_right = row_rect.right() - 34
        available_width = max(content_right - content_left, 80)

        if not is_read:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#4c9aff"))
            painter.drawEllipse(
                QRectF(row_rect.left() + 8, row_rect.top() + 12, 6, 6)
            )

        title_font = option.font
        title_font.setBold(not is_read)
        painter.setFont(title_font)
        painter.setPen(title_color)
        title = str(index.data(ARTICLE_TITLE_ROLE) or "")
        title_metrics = QFontMetrics(title_font)
        title_flags = int(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignTop
            | Qt.TextFlag.TextWordWrap
        )
        title_bounds = title_metrics.boundingRect(
            QRect(0, 0, available_width, 100_000),
            title_flags,
            title,
        )
        title_rect = QRect(
            content_left,
            row_rect.top() + 7,
            available_width,
            title_bounds.height(),
        )
        painter.drawText(title_rect, title_flags, title)

        meta_font = option.font
        meta_font.setBold(False)
        meta_font.setPointSizeF(max(meta_font.pointSizeF() - 1, 8))
        painter.setFont(meta_font)
        painter.setPen(meta_color)
        meta_metrics = QFontMetrics(meta_font)
        source_top = title_rect.bottom() + 5
        meta_flags = int(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        painter.drawText(
            QRect(
                content_left,
                source_top,
                available_width,
                meta_metrics.height(),
            ),
            meta_flags,
            str(index.data(ARTICLE_SOURCE_ROLE) or ""),
        )
        painter.drawText(
            QRect(
                content_left,
                source_top + meta_metrics.height() + 2,
                available_width,
                meta_metrics.height(),
            ),
            meta_flags,
            str(index.data(ARTICLE_META_ROLE) or ""),
        )

        painter.setPen(
            QColor("#34393f" if scheme == "dark" else "#e2e5e8")
        )
        painter.drawLine(
            row_rect.left() + 16,
            option.rect.bottom(),
            row_rect.right(),
            option.rect.bottom(),
        )

        if not (is_starred or is_hovered or is_selected):
            painter.restore()
            return

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
    translate_requested = Signal(str)
    translate_all_requested = Signal(object)
    clear_title_translation_requested = Signal(str)
    clear_all_title_translations_requested = Signal(object)
    translate_no_article = Signal()

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

        self.translate_button = QPushButton()
        self.translate_button.setObjectName("EntryFilterButton")
        self.translate_menu = QMenu(self.translate_button)
        self.translate_current_action = self.translate_menu.addAction("")
        self.translate_all_action = self.translate_menu.addAction("")
        self.translate_menu.addSeparator()
        self.clear_translation_action = self.translate_menu.addAction("")
        self.clear_all_translations_action = self.translate_menu.addAction("")
        self.translate_current_action.triggered.connect(
            self._on_translate_clicked
        )
        self.translate_all_action.triggered.connect(
            self._on_translate_all_clicked
        )
        self.clear_translation_action.triggered.connect(
            self._on_clear_translation_clicked
        )
        self.clear_all_translations_action.triggered.connect(
            self._on_clear_all_translations_clicked
        )
        self.translate_button.setMenu(self.translate_menu)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(12, 7, 10, 6)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.unread_filter_button)
        header_layout.addWidget(self.translate_button)

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
        with QSignalBlocker(self.list_widget):
            self.list_widget.clear()

            for article in self._articles:
                is_read = article.id in self._read_article_ids
                if self.unread_filter_button.isChecked() and is_read:
                    continue

                display_title = article.translated_title or article.title

                item = QListWidgetItem()
                item.setData(ARTICLE_ID_ROLE, article.id)
                item.setData(READ_STATE_ROLE, is_read)
                item.setData(ARTICLE_TITLE_ROLE, display_title)
                item.setData(ARTICLE_SOURCE_ROLE, article.source_title)
                item.setData(STARRED_STATE_ROLE, article.is_starred)
                item.setData(ARTICLE_META_ROLE, self._entry_meta_text)
                item.setToolTip(display_title)
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
        self.list_widget.setProperty(
            "colorScheme",
            self._color_scheme,
        )

        for index in range(self.list_widget.count()):
            self._apply_read_style(self.list_widget.item(index))

        self.list_widget.viewport().update()

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_filter_text(self, unread: str) -> None:
        self.unread_filter_button.setText(unread)

    def set_translate_text(
        self,
        translate: str,
        *,
        current: str | None = None,
        all_visible: str | None = None,
        clear_current: str | None = None,
        clear_all_visible: str | None = None,
    ) -> None:
        self.translate_button.setText(translate)
        self.translate_current_action.setText(current or translate)
        self.translate_all_action.setText(all_visible or translate)
        self.clear_translation_action.setText(clear_current or translate)
        self.clear_all_translations_action.setText(
            clear_all_visible or translate
        )

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

    def _on_translate_clicked(self) -> None:
        article_id = self.current_article_id()
        if article_id is not None:
            self.translate_requested.emit(article_id)
        else:
            self.translate_no_article.emit()

    def _on_translate_all_clicked(self) -> None:
        article_ids = tuple(self.visible_article_ids())
        if article_ids:
            self.translate_all_requested.emit(article_ids)
        else:
            self.translate_no_article.emit()

    def _on_clear_translation_clicked(self) -> None:
        article_id = self.current_article_id()
        if article_id is not None:
            self.clear_title_translation_requested.emit(article_id)
        else:
            self.translate_no_article.emit()

    def _on_clear_all_translations_clicked(self) -> None:
        article_ids = tuple(self.visible_article_ids())
        if article_ids:
            self.clear_all_title_translations_requested.emit(article_ids)
        else:
            self.translate_no_article.emit()

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
        item.setData(ARTICLE_META_ROLE, self._entry_meta_text)
        item.setText(
            f"{title}\n{source_title}\n{self._entry_meta_text}"
        )
