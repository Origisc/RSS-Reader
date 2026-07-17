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
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem

from mercury.models.article import Article
from mercury.ui.article_list import ArticleList


class ArticleListTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.panel = ArticleList()
        self.panel.set_articles(
            [
                Article(
                    id="long-title",
                    feed_id="feed-1",
                    title=(
                        "A deliberately long article title that must wrap "
                        "when the Entries column becomes narrow"
                    ),
                    source_title="Local fixture source",
                    content_html="<p>Fixture</p>",
                )
            ]
        )

    def tearDown(self) -> None:
        self.panel.close()
        self.panel.deleteLater()

    def test_long_title_reflows_when_entries_column_gets_narrower(self) -> None:
        option = QStyleOptionViewItem()
        index = self.panel.list_widget.model().index(0, 0)
        delegate = self.panel.list_widget.itemDelegate()

        self.panel.list_widget.viewport().resize(460, 500)
        wide_height = delegate.sizeHint(option, index).height()

        self.panel.list_widget.viewport().resize(210, 500)
        narrow_height = delegate.sizeHint(option, index).height()

        self.assertGreater(narrow_height, wide_height)

    def test_entries_disable_elision_and_horizontal_scrolling(self) -> None:
        self.assertTrue(self.panel.list_widget.wordWrap())
        self.assertEqual(
            self.panel.list_widget.textElideMode(),
            Qt.TextElideMode.ElideNone,
        )
        self.assertEqual(
            self.panel.list_widget.horizontalScrollBarPolicy(),
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )

    def test_meta_translation_preserves_selection(self) -> None:
        self.panel.list_widget.setCurrentRow(0)
        selected_item = self.panel.list_widget.currentItem()

        self.panel.set_entry_meta_text("Local cached entry")

        self.assertIs(self.panel.list_widget.currentItem(), selected_item)
        self.assertIn("Local cached entry", selected_item.text())


if __name__ == "__main__":
    unittest.main()
