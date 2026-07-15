from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QVBoxLayout,
)


class SettingsDialog(QDialog):
    """Mercury 设置窗口。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("设置")
        self.setMinimumWidth(360)

        self.language_combo = QComboBox()
        self.language_combo.addItem("简体中文", "zh_CN")
        self.language_combo.addItem("English", "en_US")

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("跟随系统", "system")
        self.theme_combo.addItem("浅色", "light")
        self.theme_combo.addItem("深色", "dark")

        form_layout = QFormLayout()
        form_layout.addRow("界面语言：", self.language_combo)
        form_layout.addRow("界面主题：", self.theme_combo)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.button_box)

    def selected_language(self) -> str:
        """返回当前选择的语言代码。"""
        return str(self.language_combo.currentData())

    def selected_theme(self) -> str:
        """返回当前选择的主题代码。"""
        return str(self.theme_combo.currentData())