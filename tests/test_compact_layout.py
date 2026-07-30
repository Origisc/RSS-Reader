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

    def test_main_menus_use_localized_text_without_icons(self) -> None:
        menus = (
            self.window.file_menu,
            self.window.settings_menu,
            self.window.view_menu,
            self.window.help_menu,
        )

        self.assertEqual(
            tuple(menu.title() for menu in menus),
            ("文件", "设置", "视图", "帮助"),
        )
        self.assertTrue(all(menu.icon().isNull() for menu in menus))

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
        self.assertFalse(self.window.tag_editor.isVisible())
        self.assertFalse(self.window.toggle_tags_action.isChecked())
        self.assertFalse(
            self.window.article_reader.tag_toggle_button.isChecked()
        )

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

    def test_reference_layout_uses_header_and_comfortable_three_columns(
        self,
    ) -> None:
        self.assertIs(
            self.window.centralWidget(),
            self.window.app_shell,
        )
        self.assertEqual(self.window.app_header.height(), 48)
        self.assertEqual(self.window.app_brand.text(), "Mercury")
        self.assertIs(
            self.window.header_refresh_button.defaultAction(),
            self.window.refresh_action,
        )
        self.assertIs(
            self.window.header_settings_button.defaultAction(),
            self.window.open_settings_action,
        )
        self.assertGreaterEqual(self.window.sidebar.minimumWidth(), 210)
        self.assertGreaterEqual(self.window.article_list.minimumWidth(), 300)
        self.assertGreaterEqual(self.window.article_reader.minimumWidth(), 560)
        self.assertTrue(self.window.splitter.childrenCollapsible())

    def test_navigation_columns_can_collapse_to_zero_and_expand_again(
        self,
    ) -> None:
        self.window.splitter.setSizes([0, 0, 1200])
        self.app.processEvents()

        collapsed_sizes = self.window.splitter.sizes()
        self.assertEqual(collapsed_sizes[0], 0)
        self.assertEqual(collapsed_sizes[1], 0)
        self.assertGreater(collapsed_sizes[2], 0)

        self.window.splitter.setSizes([230, 360, 850])
        self.app.processEvents()

        expanded_sizes = self.window.splitter.sizes()
        self.assertGreaterEqual(
            expanded_sizes[0],
            self.window.sidebar.minimumWidth(),
        )
        self.assertGreaterEqual(
            expanded_sizes[1],
            self.window.article_list.minimumWidth(),
        )


if __name__ == "__main__":
    unittest.main()
