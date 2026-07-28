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
from PySide6.QtTest import QSignalSpy
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

    def test_unread_filter_updates_when_read_state_changes(self) -> None:
        self.panel.unread_filter_button.setChecked(True)
        self.assertEqual(self.panel.list_widget.count(), 1)

        self.panel.set_read_state("long-title", True)
        self.assertEqual(self.panel.list_widget.count(), 0)

        self.panel.set_read_state("long-title", False)
        self.assertEqual(self.panel.list_widget.count(), 1)

    def test_title_translation_menu_emits_current_and_all_entries(
        self,
    ) -> None:
        self.panel.set_translate_text(
            "Translate title",
            current="Translate selected title",
            all_visible="Translate all titles",
            clear_current="Remove selected translation",
            clear_all_visible="Remove all translations",
        )
        self.panel.list_widget.setCurrentRow(0)
        current_spy = QSignalSpy(self.panel.translate_requested)
        all_spy = QSignalSpy(self.panel.translate_all_requested)
        clear_spy = QSignalSpy(
            self.panel.clear_title_translation_requested
        )
        clear_all_spy = QSignalSpy(
            self.panel.clear_all_title_translations_requested
        )

        self.panel.translate_current_action.trigger()
        self.panel.translate_all_action.trigger()
        self.panel.clear_translation_action.trigger()
        self.panel.clear_all_translations_action.trigger()

        self.assertEqual(current_spy.count(), 1)
        self.assertEqual(current_spy.at(0)[0], "long-title")
        self.assertEqual(all_spy.count(), 1)
        self.assertEqual(tuple(all_spy.at(0)[0]), ("long-title",))
        self.assertEqual(clear_spy.count(), 1)
        self.assertEqual(clear_spy.at(0)[0], "long-title")
        self.assertEqual(clear_all_spy.count(), 1)
        self.assertEqual(
            tuple(clear_all_spy.at(0)[0]),
            ("long-title",),
        )
        self.assertEqual(
            self.panel.translate_current_action.text(),
            "Translate selected title",
        )
        self.assertEqual(
            self.panel.translate_all_action.text(),
            "Translate all titles",
        )
        self.assertEqual(
            self.panel.clear_translation_action.text(),
            "Remove selected translation",
        )
        self.assertEqual(
            self.panel.clear_all_translations_action.text(),
            "Remove all translations",
        )


if __name__ == "__main__":
    unittest.main()
