from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
)

from mercury.models.tag import Tag


class TagEditorPanel(QFrame):
    """Edit local tags assigned to the article shown in the Reader."""

    close_requested = Signal()
    add_tag_requested = Signal(str)
    tag_assignment_changed = Signal(str, bool)

    def __init__(self) -> None:
        super().__init__()

        self._article_available = False
        self._empty_text = ""
        self._no_article_text = ""

        self.setObjectName("TagEditorPopover")
        self.setMaximumWidth(340)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Maximum,
        )

        self.title_label = QLabel()
        self.title_label.setObjectName("TagPanelTitle")
        self.close_button = QToolButton()
        self.close_button.setObjectName("TagPanelCloseButton")
        self.close_button.setText("×")
        self.close_button.clicked.connect(self.close_requested.emit)

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(6)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch(1)
        title_layout.addWidget(self.close_button)

        self.tag_input = QLineEdit()
        self.tag_input.setObjectName("TagInput")
        self.tag_input.textChanged.connect(self._update_add_button)
        self.tag_input.returnPressed.connect(self._request_add)
        self.add_button = QPushButton()
        self.add_button.setObjectName("TagAddButton")
        self.add_button.setEnabled(False)
        self.add_button.clicked.connect(self._request_add)

        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(6)
        input_layout.addWidget(self.tag_input, 1)
        input_layout.addWidget(self.add_button)

        self.existing_label = QLabel()
        self.existing_label.setObjectName("TagSectionTitle")
        self.no_tags_label = QLabel()
        self.no_tags_label.setObjectName("TagEmpty")
        self.no_tags_label.setWordWrap(True)

        self.chip_grid = QGridLayout()
        self.chip_grid.setContentsMargins(0, 0, 0, 0)
        self.chip_grid.setHorizontalSpacing(5)
        self.chip_grid.setVerticalSpacing(5)
        self.chip_grid.setColumnStretch(4, 1)

        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(10, 9, 10, 10)
        self.content_layout.setSpacing(6)
        self.content_layout.addLayout(title_layout)
        self.content_layout.addLayout(input_layout)
        self.content_layout.addWidget(self.existing_label)
        self.content_layout.addLayout(self.chip_grid)
        self.content_layout.addWidget(self.no_tags_label)
        self.set_article_tags([], set(), article_available=False)

    def set_suggestion_widget(self, widget) -> None:
        self.content_layout.addWidget(widget)

    def set_texts(
        self,
        *,
        title: str,
        input_placeholder: str,
        add: str,
        existing: str,
        empty: str,
        no_article: str,
        close_tooltip: str,
    ) -> None:
        self.title_label.setText(title)
        self.tag_input.setPlaceholderText(input_placeholder)
        self.add_button.setText(add)
        self.existing_label.setText(existing)
        self._empty_text = empty
        self._no_article_text = no_article
        self.close_button.setToolTip(close_tooltip)
        self.close_button.setAccessibleName(close_tooltip)
        self._update_empty_text()

    def set_article_tags(
        self,
        tags: list[Tag],
        assigned_tag_ids: set[str],
        *,
        article_available: bool,
    ) -> None:
        self._article_available = article_available
        self.tag_input.setEnabled(article_available)
        self._clear_chips()

        for index, tag in enumerate(tags):
            chip = QPushButton(tag.name)
            chip.setObjectName("TagChip")
            chip.setProperty("chip", True)
            chip.setCheckable(True)
            chip.setChecked(tag.id in assigned_tag_ids)
            chip.setEnabled(article_available)
            chip.setToolTip(tag.name)
            chip.clicked.connect(
                lambda checked=False, tag_id=tag.id: (
                    self.tag_assignment_changed.emit(tag_id, checked)
                )
            )
            self.chip_grid.addWidget(chip, index // 4, index % 4)

        self.no_tags_label.setVisible(not tags or not article_available)
        self._update_empty_text()
        self._update_add_button()

    def clear_input(self) -> None:
        self.tag_input.clear()

    def _request_add(self) -> None:
        value = self.tag_input.text().strip()
        if not self._article_available or not value:
            return
        self.add_tag_requested.emit(value)

    def _update_add_button(self) -> None:
        self.add_button.setEnabled(
            self._article_available
            and bool(self.tag_input.text().strip())
        )

    def _update_empty_text(self) -> None:
        text = (
            self._empty_text
            if self._article_available
            else self._no_article_text
        )
        self.no_tags_label.setText(text)

    def _clear_chips(self) -> None:
        while self.chip_grid.count():
            item = self.chip_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
