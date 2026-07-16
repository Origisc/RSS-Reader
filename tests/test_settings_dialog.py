import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QStyle,
    QStyleOptionSpinBox,
)

from mercury.i18n import Translator
from mercury.ui.reader_style import ReaderStyle
from mercury.ui.settings_dialog import SettingsDialog
from mercury.ui.theme import stylesheet_for_theme


class SettingsDialogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_returns_selected_reader_style(self) -> None:
        dialog = SettingsDialog(
            Translator("en_US"),
            "en_US",
            "dark",
            current_reader_style=ReaderStyle(
                font_size=22,
                line_height=1.8,
                content_width=720,
            ),
        )

        selected = dialog.selected_reader_style()

        self.assertEqual(selected.font_size, 22)
        self.assertEqual(selected.line_height, 1.8)
        self.assertEqual(selected.content_width, 720)
        dialog.close()
        dialog.deleteLater()

    def test_spin_controls_can_increment_and_decrement(self) -> None:
        dialog = SettingsDialog(
            Translator("zh_CN"),
            "zh_CN",
            "dark",
            current_reader_style=ReaderStyle(
                font_size=18,
                line_height=1.6,
                content_width=820,
            ),
        )

        dialog.font_size_spin.stepUp()
        dialog.line_height_spin.stepUp()
        dialog.content_width_spin.stepDown()

        self.assertEqual(dialog.font_size_spin.value(), 19)
        self.assertEqual(dialog.line_height_spin.value(), 1.7)
        self.assertEqual(dialog.content_width_spin.value(), 800)
        dialog.close()
        dialog.deleteLater()

    def test_spin_up_button_accepts_mouse_click(self) -> None:
        dialog = SettingsDialog(
            Translator("zh_CN"),
            "zh_CN",
            "dark",
            current_reader_style=ReaderStyle(font_size=18),
        )
        self.app.setStyleSheet(stylesheet_for_theme("dark"))

        try:
            dialog.show()
            self.app.processEvents()
            spin_box = dialog.font_size_spin
            option = QStyleOptionSpinBox()
            spin_box.initStyleOption(option)
            up_button_rect = spin_box.style().subControlRect(
                QStyle.ComplexControl.CC_SpinBox,
                option,
                QStyle.SubControl.SC_SpinBoxUp,
                spin_box,
            )

            QTest.mouseClick(
                spin_box,
                Qt.MouseButton.LeftButton,
                pos=up_button_rect.center(),
            )

            self.assertGreaterEqual(up_button_rect.width(), 28)
            self.assertEqual(spin_box.value(), 19)
        finally:
            dialog.close()
            dialog.deleteLater()
            self.app.setStyleSheet("")


if __name__ == "__main__":
    unittest.main()
