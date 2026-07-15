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

    def test_system_theme_uses_default_dark_reader_style(self) -> None:
        self.assertIn("QTextBrowser#ReaderContent", stylesheet_for_theme("system"))

    def test_unknown_theme_returns_empty_stylesheet(self) -> None:
        self.assertEqual(stylesheet_for_theme("unknown"), "")
