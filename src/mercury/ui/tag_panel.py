from collections.abc import Sequence

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


class TagEditorPanel(QFrame):
    """Compact article-tag editor presented over the Reader surface."""

    close_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

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
        self.add_button = QPushButton()
        self.add_button.setObjectName("TagAddButton")
        self.add_button.setEnabled(False)

        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(6)
        input_layout.addWidget(self.tag_input, 1)
        input_layout.addWidget(self.add_button)

        self.suggested_label = QLabel()
        self.suggested_label.setObjectName("TagSectionTitle")
        self.existing_label = QLabel()
        self.existing_label.setObjectName("TagSectionTitle")
        self.no_tags_label = QLabel()
        self.no_tags_label.setObjectName("TagEmpty")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 9, 10, 10)
        layout.setSpacing(6)
        layout.addLayout(title_layout)
        layout.addLayout(input_layout)
        layout.addWidget(self.suggested_label)
        layout.addLayout(
            self._chip_grid(["History", "Internet", "AOL", "America"])
        )
        layout.addWidget(self.existing_label)
        layout.addLayout(
            self._chip_grid(
                [
                    "AI",
                    "Programming",
                    "Open Source",
                    "Apple",
                    "Politics",
                    "Hardware",
                    "Business",
                    "Writing",
                ]
            )
        )
        layout.addWidget(self.no_tags_label)

    def set_texts(
        self,
        *,
        title: str,
        input_placeholder: str,
        add: str,
        suggested: str,
        existing: str,
        empty: str,
        close_tooltip: str,
    ) -> None:
        self.title_label.setText(title)
        self.tag_input.setPlaceholderText(input_placeholder)
        self.add_button.setText(add)
        self.suggested_label.setText(suggested)
        self.existing_label.setText(existing)
        self.no_tags_label.setText(empty)
        self.close_button.setToolTip(close_tooltip)
        self.close_button.setAccessibleName(close_tooltip)

    @staticmethod
    def tag_names() -> tuple[str, ...]:
        return (
            "AI",
            "Programming",
            "Open Source",
            "Apple",
            "Politics",
            "Hardware",
            "Business",
            "Writing",
        )

    def _chip_grid(self, labels: Sequence[str]) -> QGridLayout:
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(5)
        grid.setVerticalSpacing(5)

        for index, label_text in enumerate(labels):
            chip = QLabel(label_text)
            chip.setProperty("chip", True)
            grid.addWidget(chip, index // 4, index % 4)

        grid.setColumnStretch(4, 1)
        return grid
