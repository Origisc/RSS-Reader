import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtWidgets import QApplication

from mercury.services.mock_article_service import MockArticleService
from mercury.ui.main_window import MainWindow


class CompactLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.window = MainWindow(MockArticleService())
        self.window.show()
        self.app.processEvents()

    def tearDown(self) -> None:
        self.window.close()
        self.window.deleteLater()

    def test_redundant_toolbar_and_wide_tag_dock_are_removed(self) -> None:
        self.assertFalse(hasattr(self.window, "main_toolbar"))
        self.assertFalse(hasattr(self.window, "tags_dock"))
        self.assertIn(
            self.window.add_feed_action,
            self.window.file_menu.actions(),
        )
        self.assertIn(
            self.window.toggle_tags_action,
            self.window.view_menu.actions(),
        )

    def test_tag_editor_is_a_compact_reader_overlay(self) -> None:
        self.assertIs(
            self.window.tag_editor.parentWidget(),
            self.window.article_reader.reader_body,
        )
        self.assertLessEqual(self.window.tag_editor.maximumWidth(), 340)
        self.assertLess(
            self.window.tag_editor.width(),
            self.window.article_reader.width(),
        )

        self.window.tag_editor.close_button.click()
        self.app.processEvents()
        self.assertFalse(self.window.tag_editor.isVisible())
        self.assertFalse(self.window.toggle_tags_action.isChecked())

        self.window.article_reader.tag_toggle_button.click()
        self.app.processEvents()
        self.assertTrue(self.window.tag_editor.isVisible())
        self.assertTrue(self.window.toggle_tags_action.isChecked())

    def test_summary_starts_as_a_collapsed_reader_strip(self) -> None:
        self.assertTrue(self.window.summary_section.isVisible())
        self.assertFalse(self.window.summary_panel.isVisible())
        self.assertFalse(self.window.toggle_summary_action.isChecked())
        self.assertLessEqual(
            self.window.summary_section.height(),
            self.window.summary_title_bar.sizeHint().height() + 1,
        )


if __name__ == "__main__":
    unittest.main()
