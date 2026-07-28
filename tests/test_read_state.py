import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from mercury.services.mock_article_service import MockArticleService
from mercury.ui.main_window import MainWindow
from mercury.ui.read_state import InMemoryReadStateStore
from mercury.ui.sidebar import FEED_ID_ROLE


class ReadStateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_in_memory_store_can_mark_read_and_unread(self) -> None:
        store = InMemoryReadStateStore()

        store.set_read("article-1", True)
        self.assertTrue(store.is_read("article-1"))

        store.set_read("article-1", False)
        self.assertFalse(store.is_read("article-1"))

    def test_open_marks_article_read_and_updates_feed_count(self) -> None:
        store = InMemoryReadStateStore()
        window = MainWindow(
            MockArticleService(),
            read_state_store=store,
        )
        feed_item = next(
            window.sidebar.feed_list.item(row)
            for row in range(window.sidebar.feed_list.count())
            if window.sidebar.feed_list.item(row).data(FEED_ID_ROLE)
            == "openai"
        )

        first_item = window.article_list.list_widget.item(0)
        self.assertTrue(first_item.font().bold())
        self.assertIn("1 未读", feed_item.text())

        window._show_article("mercury-start")

        self.assertTrue(store.is_read("mercury-start"))
        self.assertFalse(first_item.font().bold())
        self.assertEqual(
            first_item.foreground().color().name().lower(),
            "#778391",
        )
        self.assertIn("0 未读", feed_item.text())

        window.article_list.set_color_scheme("light")
        self.assertEqual(
            first_item.foreground().color().name().lower(),
            "#8a949e",
        )

        window.close()
        window.deleteLater()
        self.app.setStyleSheet("")

    def test_reader_button_can_restore_article_to_unread(self) -> None:
        store = InMemoryReadStateStore({"mercury-start"})
        window = MainWindow(
            MockArticleService(),
            read_state_store=store,
        )
        feed_item = next(
            window.sidebar.feed_list.item(row)
            for row in range(window.sidebar.feed_list.count())
            if window.sidebar.feed_list.item(row).data(FEED_ID_ROLE)
            == "openai"
        )
        window._show_article("mercury-start")

        window.article_reader.read_state_button.click()

        self.assertFalse(store.is_read("mercury-start"))
        self.assertIn("1 未读", feed_item.text())
        self.assertEqual(
            window.article_reader.read_state_button.text(),
            "标记为已读",
        )

        window.close()
        window.deleteLater()
        self.app.setStyleSheet("")

    def test_title_translation_does_not_target_reader_only_article(self) -> None:
        window = MainWindow(MockArticleService())
        window.article_list.unread_filter_button.setChecked(True)
        first_item = window.article_list.list_widget.item(0)
        article_id = str(first_item.data(Qt.ItemDataRole.UserRole))

        window.article_list.list_widget.setCurrentItem(first_item)
        self.app.processEvents()

        self.assertEqual(
            window.article_reader.current_article_id,
            article_id,
        )
        self.assertIsNone(window.article_list.current_article_id())

        with (
            patch.object(window, "_translate_current_article") as translate,
            patch(
                "mercury.ui.main_window.QMessageBox.information"
            ) as information,
        ):
            window.article_list.translate_current_action.trigger()
            self.app.processEvents()

        translate.assert_not_called()
        information.assert_called_once()
        self.assertEqual(information.call_args.args[1], "翻译标题")
        window.close()
        window.deleteLater()
        self.app.setStyleSheet("")


if __name__ == "__main__":
    unittest.main()
