import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.ui.theme import stylesheet_for_theme


class ThemeTest(unittest.TestCase):
    def test_dark_theme_contains_reader_panel_styles(self) -> None:
        stylesheet = stylesheet_for_theme("dark")

        self.assertIn("QWidget#ReaderPanel", stylesheet)
        self.assertIn('QLabel[chip="true"]', stylesheet)
        self.assertIn("QToolBar#AppToolbar QToolButton", stylesheet)
        self.assertIn("color: #e5edf5", stylesheet)

    def test_light_theme_sets_toolbar_action_text_color(self) -> None:
        stylesheet = stylesheet_for_theme("light")

        self.assertIn("QToolBar QToolButton", stylesheet)
        self.assertIn("color: #1f2933", stylesheet)
        self.assertIn("QToolButton#FeedAddButton", stylesheet)
        self.assertIn("QToolButton#FeedMenuButton", stylesheet)

    def test_dark_settings_dialog_uses_readable_label_and_input_colors(
        self,
    ) -> None:
        stylesheet = stylesheet_for_theme("dark")

        self.assertIn("QDialog QLabel", stylesheet)
        self.assertIn("color: #e5edf5", stylesheet)
        self.assertIn("QDialog QDoubleSpinBox", stylesheet)
        self.assertIn("background: #202833", stylesheet)
        self.assertIn("QDialog QComboBox QAbstractItemView", stylesheet)
        self.assertIn("selection-color: #ffffff", stylesheet)
        self.assertIn("QDialog QDoubleSpinBox::up-button", stylesheet)
        self.assertIn("subcontrol-position: top right", stylesheet)
        self.assertIn("subcontrol-position: bottom right", stylesheet)

    def test_light_settings_dialog_uses_dark_label_text(self) -> None:
        stylesheet = stylesheet_for_theme("light")

        self.assertIn("QDialog QLabel", stylesheet)
        self.assertIn("color: #1f2933", stylesheet)

    def test_system_theme_uses_default_dark_reader_style(self) -> None:
        self.assertIn("QTextBrowser#ReaderContent", stylesheet_for_theme("system"))

    def test_unknown_theme_returns_empty_stylesheet(self) -> None:
        self.assertEqual(stylesheet_for_theme("unknown"), "")
