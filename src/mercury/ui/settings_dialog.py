from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QSpinBox,
    QVBoxLayout,
)

from mercury.i18n.translations import SUPPORTED_LANGUAGES, Translator
from mercury.ui.reader_style import (
    MAX_CONTENT_WIDTH,
    MAX_FONT_SIZE,
    MAX_LINE_HEIGHT,
    MIN_CONTENT_WIDTH,
    MIN_FONT_SIZE,
    MIN_LINE_HEIGHT,
    ReaderStyle,
)
from mercury.ui.theme import THEME_CODES


class SettingsDialog(QDialog):
    """Mercury 设置窗口。"""

    def __init__(
        self,
        translator: Translator,
        current_language: str,
        current_theme: str,
        current_reader_style: ReaderStyle | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._translator = translator
        self.setMinimumWidth(360)
        reader_style = (current_reader_style or ReaderStyle()).normalized()

        self.language_combo = QComboBox()
        for language_code, language_name in SUPPORTED_LANGUAGES.items():
            self.language_combo.addItem(language_name, language_code)

        self.theme_combo = QComboBox()
        for theme_code in THEME_CODES:
            self.theme_combo.addItem(
                self._translator.text(f"theme.{theme_code}"),
                theme_code,
            )

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(MIN_FONT_SIZE, MAX_FONT_SIZE)
        self.font_size_spin.setSuffix(" px")
        self.font_size_spin.setValue(reader_style.font_size)

        self.line_height_spin = QDoubleSpinBox()
        self.line_height_spin.setRange(MIN_LINE_HEIGHT, MAX_LINE_HEIGHT)
        self.line_height_spin.setDecimals(2)
        self.line_height_spin.setSingleStep(0.1)
        self.line_height_spin.setValue(reader_style.line_height)

        self.content_width_spin = QSpinBox()
        self.content_width_spin.setRange(MIN_CONTENT_WIDTH, MAX_CONTENT_WIDTH)
        self.content_width_spin.setSingleStep(20)
        self.content_width_spin.setSuffix(" px")
        self.content_width_spin.setValue(reader_style.content_width)

        self.form_layout = QFormLayout()
        self.form_layout.addRow(
            self._translator.text("settings.language"),
            self.language_combo,
        )
        self.form_layout.addRow(
            self._translator.text("settings.theme"),
            self.theme_combo,
        )
        self.form_layout.addRow(
            self._translator.text("settings.reader_font_size"),
            self.font_size_spin,
        )
        self.form_layout.addRow(
            self._translator.text("settings.reader_line_height"),
            self.line_height_spin,
        )
        self.form_layout.addRow(
            self._translator.text("settings.reader_content_width"),
            self.content_width_spin,
        )

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self.form_layout)
        main_layout.addWidget(self.button_box)

        self._select_combo_value(self.language_combo, current_language)
        self._select_combo_value(self.theme_combo, current_theme)
        self._translate_ui()

    def selected_language(self) -> str:
        """返回当前选择的语言代码。"""
        return str(self.language_combo.currentData())

    def selected_theme(self) -> str:
        """返回当前选择的主题代码。"""
        return str(self.theme_combo.currentData())

    def selected_reader_style(self) -> ReaderStyle:
        return ReaderStyle(
            font_size=self.font_size_spin.value(),
            line_height=self.line_height_spin.value(),
            content_width=self.content_width_spin.value(),
        ).normalized()

    def _translate_ui(self) -> None:
        self.setWindowTitle(self._translator.text("settings.title"))

        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        cancel_button = self.button_box.button(
            QDialogButtonBox.StandardButton.Cancel
        )

        ok_button.setText(self._translator.text("settings.ok"))
        cancel_button.setText(self._translator.text("settings.cancel"))

    def _select_combo_value(self, combo: QComboBox, value: str) -> None:
        index = combo.findData(value)

        if index >= 0:
            combo.setCurrentIndex(index)
