from dataclasses import dataclass

from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from mercury.i18n import Translator


@dataclass(frozen=True, slots=True)
class ShortcutEntry:
    key: str
    description: str


class ShortcutHelpDialog(QDialog):
    """Display the shortcuts currently exposed by the main window."""

    def __init__(
        self,
        translator: Translator,
        entries: tuple[ShortcutEntry, ...],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("ShortcutHelpDialog")
        self.setWindowTitle(translator.text("shortcuts.title"))
        self.setMinimumSize(560, 300)

        self.intro_label = QLabel(translator.text("shortcuts.description"))
        self.intro_label.setObjectName("ShortcutHelpIntro")
        self.intro_label.setWordWrap(True)

        self.table = QTableWidget(len(entries), 2)
        self.table.setObjectName("ShortcutTable")
        self.table.setHorizontalHeaderLabels(
            [
                translator.text("shortcuts.key_header"),
                translator.text("shortcuts.function_header"),
            ]
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        for row, entry in enumerate(entries):
            self.table.setItem(row, 0, QTableWidgetItem(entry.key))
            self.table.setItem(
                row,
                1,
                QTableWidgetItem(entry.description),
            )

        self.table.resizeRowsToContents()

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        self.button_box.rejected.connect(self.reject)
        close_button = self.button_box.button(
            QDialogButtonBox.StandardButton.Close
        )
        close_button.setText(translator.text("shortcuts.close"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(self.intro_label)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.button_box)
