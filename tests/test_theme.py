import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.ui.theme import (
    UI_FONT_FAMILIES,
    preferred_ui_font,
    stylesheet_for_theme,
)


class ThemeTest(unittest.TestCase):
    def test_preferred_ui_font_uses_cross_platform_sans_serif_fallbacks(
        self,
    ) -> None:
        font = preferred_ui_font()

        self.assertEqual(tuple(font.families()), UI_FONT_FAMILIES)
        self.assertEqual(font.pointSize(), 10)
        self.assertIn("Segoe UI", font.families())
        self.assertIn("PingFang SC", font.families())
        self.assertIn("Noto Sans CJK SC", font.families())

    def test_dark_theme_contains_reader_panel_styles(self) -> None:
        stylesheet = stylesheet_for_theme("dark")

        self.assertIn("QFrame#AppHeader", stylesheet)
        self.assertIn("QLabel#AppBrand", stylesheet)
        self.assertIn("QToolButton#TopActionButton", stylesheet)
        self.assertIn("QWidget#ReaderPanel", stylesheet)
        self.assertIn('QLabel[chip="true"]', stylesheet)
        self.assertIn("QFrame#TagEditorPopover", stylesheet)
        self.assertIn("QPushButton#ReaderUtilityButton", stylesheet)
        self.assertIn("color: #e5edf5", stylesheet)

    def test_light_theme_sets_compact_navigation_colors(self) -> None:
        stylesheet = stylesheet_for_theme("light")

        self.assertIn("QFrame#AppHeader", stylesheet)
        self.assertIn("QPushButton#PrimarySegment", stylesheet)
        self.assertIn("QPushButton#EntryFilterButton", stylesheet)
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
        self.assertIn("QDialog QLineEdit", stylesheet)
        self.assertIn("QDialog QCheckBox", stylesheet)
        self.assertIn("QDialog QCheckBox:disabled", stylesheet)
        self.assertIn("QDialog QLineEdit:disabled", stylesheet)
        self.assertIn("QDialog QPushButton:disabled", stylesheet)
        self.assertIn("background: #202833", stylesheet)
        self.assertIn("QDialog QComboBox QAbstractItemView", stylesheet)
        self.assertIn("selection-color: #ffffff", stylesheet)
        self.assertIn("QDialog QDoubleSpinBox::up-button", stylesheet)
        self.assertIn("subcontrol-position: top right", stylesheet)
        self.assertIn("subcontrol-position: bottom right", stylesheet)
        self.assertIn("QListWidget#AgentsSettingsList::item:hover", stylesheet)
        self.assertIn("border-right: 1px solid #2d3036", stylesheet)
        self.assertNotIn(
            "QListWidget#AgentsSettingsList {\n"
            "    background: #202126;\n"
            "    border: 1px solid #30333a",
            stylesheet,
        )

    def test_light_settings_dialog_uses_dark_label_text(self) -> None:
        stylesheet = stylesheet_for_theme("light")

        self.assertIn("QDialog QLabel", stylesheet)
        self.assertIn("color: #1f2933", stylesheet)
        self.assertIn("QDialog QLineEdit", stylesheet)
        self.assertIn("QDialog QCheckBox", stylesheet)
        self.assertIn("QDialog QCheckBox:disabled", stylesheet)
        self.assertIn("QDialog QLineEdit:disabled", stylesheet)
        self.assertIn("QDialog QPushButton:disabled", stylesheet)

    def test_system_theme_uses_default_dark_reader_style(self) -> None:
        self.assertIn("QTextBrowser#ReaderContent", stylesheet_for_theme("system"))

    def test_summary_panel_controls_are_readable_in_both_themes(self) -> None:
        for theme in ("light", "dark"):
            stylesheet = stylesheet_for_theme(theme)

            self.assertIn("QFrame#SummarySection", stylesheet)
            self.assertIn("QFrame#SummarySectionTitleBar", stylesheet)
            self.assertIn("QPushButton#SummarySectionToggleButton", stylesheet)
            self.assertIn("QSplitter#ReaderSummarySplitter", stylesheet)
            self.assertIn("QFrame#SummaryPanel", stylesheet)
            self.assertIn("QPlainTextEdit#SummaryContent", stylesheet)
            self.assertIn("QPushButton#SummaryActionButton", stylesheet)
            self.assertIn("QComboBox#SummaryControl", stylesheet)
            self.assertIn(
                "QComboBox#SummaryControl QAbstractItemView",
                stylesheet,
            )

    def test_unknown_theme_returns_empty_stylesheet(self) -> None:
        self.assertEqual(stylesheet_for_theme("unknown"), "")
