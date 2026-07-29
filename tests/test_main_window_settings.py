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

from domain.feed.import_errors import (
    FeedImportError,
    FeedImportErrorCode,
)
from mercury.services.mock_article_service import MockArticleService
from mercury.ui.article_list import ARTICLE_ID_ROLE
from mercury.ui.main_window import MainWindow
from mercury.ui.reader_style import ReaderStyle


class MainWindowSettingsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.window = MainWindow(MockArticleService())

    def tearDown(self) -> None:
        self.window.close()
        self.window.deleteLater()
        self.app.setStyleSheet("")

    def test_font_size_preserves_article_and_selection(self) -> None:
        article_list = self.window.article_list.list_widget
        article_list.setCurrentRow(0)
        selected_item = article_list.currentItem()
        selected_article_id = selected_item.data(ARTICLE_ID_ROLE)

        self.window._apply_settings(
            "en_US",
            "light",
            ReaderStyle(font_size=24),
        )

        self.assertEqual(
            self.window.article_reader.current_article_id,
            selected_article_id,
        )
        self.assertIs(article_list.currentItem(), selected_item)
        self.assertEqual(
            article_list.currentItem().data(ARTICLE_ID_ROLE),
            selected_article_id,
        )
        self.assertEqual(
            self.window.article_reader.reader_style.font_size,
            24,
        )
        self.assertIn("Local cached entry", selected_item.text())

    def test_feed_import_error_is_localized_with_exact_path(self) -> None:
        error = FeedImportError(
            FeedImportErrorCode.FILE_NOT_FOUND,
            source="E:\\feeds\\missing.xml",
        )

        chinese_message = self.window._service_error_message(error)
        self.window.translator.set_language("en_US")
        english_message = self.window._service_error_message(error)

        self.assertIn("找不到本地文件", chinese_message)
        self.assertIn("E:\\feeds\\missing.xml", chinese_message)
        self.assertIn("local file was not found", english_message)
        self.assertIn("E:\\feeds\\missing.xml", english_message)


if __name__ == "__main__":
    unittest.main()
