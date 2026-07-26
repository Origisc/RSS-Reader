import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

for path in (PROJECT_ROOT, SRC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from core.database import DBManager
from domain.feed.use_cases import FeedUseCase
from mercury.models.article import Article
from mercury.services.article_service import StarredEntryError
from mercury.services.backend_article_service import BackendArticleService
from mercury.services.mock_article_service import MockArticleService
from mercury.ui.article_list import ArticleList, STARRED_STATE_ROLE
from mercury.ui.main_window import MainWindow
from mercury.ui.read_state import InMemoryReadStateStore
from mercury.ui.sidebar import FEED_ID_ROLE, STARRED_FEED_ID


class StarredPersistenceTest(unittest.TestCase):
    def _add_article(
        self,
        database: DBManager,
        *,
        link: str = "https://example.com/article",
        published: str = "2026-07-26T10:00:00",
    ) -> tuple[int, int]:
        feed_id = database.add_feed(
            "Example",
            "https://example.com/feed",
        )
        database.save_articles(
            feed_id,
            [
                {
                    "title": "Star fixture",
                    "link": link,
                    "summary": "<p>Fixture</p>",
                    "published": published,
                }
            ],
        )
        article_id = int(database.get_articles_by_feed(feed_id)[0][0])
        return int(feed_id), article_id

    def test_starred_state_survives_database_recreation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "mercury.db"
            first = DBManager(str(database_path))
            _feed_id, article_id = self._add_article(first)

            self.assertTrue(first.set_article_starred(article_id, True))
            first.conn.close()

            second = DBManager(str(database_path))
            try:
                self.assertEqual(second.count_starred_articles(), 1)
                self.assertEqual(
                    second.get_article_full_detail(article_id)[-1],
                    1,
                )
            finally:
                second.conn.close()

    def test_duplicate_feed_sync_preserves_starred_state(self) -> None:
        database = DBManager(":memory:")
        try:
            feed_id, article_id = self._add_article(database)
            database.set_article_starred(article_id, True)

            database.save_articles(
                feed_id,
                [
                    {
                        "title": "Incoming duplicate",
                        "link": "https://example.com/article",
                        "summary": "Incoming",
                    }
                ],
            )

            self.assertEqual(database.count_starred_articles(), 1)
            self.assertEqual(
                database.get_article_full_detail(article_id)[-1],
                1,
            )
        finally:
            database.conn.close()

    def test_backend_lists_counts_and_unstars_global_entries(self) -> None:
        database = DBManager(":memory:")
        service = BackendArticleService(
            database,
            FeedUseCase(database),
        )
        try:
            _feed_id, article_id = self._add_article(database)

            service.set_starred(str(article_id), True)

            self.assertEqual(service.count_starred_articles(), 1)
            self.assertEqual(
                [article.id for article in service.list_starred_articles()],
                [str(article_id)],
            )
            self.assertTrue(service.get_article(str(article_id)).is_starred)

            service.set_starred(str(article_id), False)
            self.assertEqual(service.list_starred_articles(), [])
        finally:
            database.conn.close()

    def test_backend_rejects_missing_or_invalid_article(self) -> None:
        database = DBManager(":memory:")
        service = BackendArticleService(
            database,
            FeedUseCase(database),
        )
        try:
            with self.assertRaises(StarredEntryError):
                service.set_starred("999", True)
            with self.assertRaises(StarredEntryError):
                service.set_starred("not-an-id", True)
        finally:
            database.conn.close()


class StarredUITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_row_star_click_does_not_change_selected_entry(self) -> None:
        panel = ArticleList()
        panel.resize(360, 280)
        panel.set_articles(
            [
                Article(
                    id="first",
                    feed_id="feed",
                    title="First",
                    source_title="Fixture",
                    content_html="<p>First</p>",
                ),
                Article(
                    id="second",
                    feed_id="feed",
                    title="Second",
                    source_title="Fixture",
                    content_html="<p>Second</p>",
                ),
            ]
        )
        toggles: list[tuple[str, bool]] = []
        panel.star_toggled.connect(
            lambda article_id, state: toggles.append(
                (article_id, state)
            )
        )
        panel.show()
        self.app.processEvents()
        panel.list_widget.setCurrentRow(0)
        target = panel.list_widget.item(1)
        rect = panel.list_widget.visualItemRect(target)

        QTest.mouseClick(
            panel.list_widget.viewport(),
            Qt.MouseButton.LeftButton,
            pos=QPoint(rect.right() - 12, rect.center().y()),
        )

        self.assertEqual(toggles, [("second", True)])
        self.assertEqual(panel.current_article_id(), "first")
        panel.close()
        panel.deleteLater()

    def test_row_star_state_updates_without_rebuilding_selection(self) -> None:
        panel = ArticleList()
        article = Article(
            id="entry",
            feed_id="feed",
            title="Entry",
            source_title="Fixture",
            content_html="<p>Entry</p>",
        )
        panel.set_articles([article])
        panel.list_widget.setCurrentRow(0)
        selected_item = panel.list_widget.currentItem()

        panel.set_starred_state("entry", True)

        self.assertIs(panel.list_widget.currentItem(), selected_item)
        self.assertTrue(selected_item.data(STARRED_STATE_ROLE))
        panel.close()
        panel.deleteLater()

    def test_starred_selection_handoff_order(self) -> None:
        fallback = MainWindow._starred_selection_fallback

        self.assertEqual(
            fallback(["one", "two", "three"], "two", "two"),
            "three",
        )
        self.assertEqual(
            fallback(["one", "two", "three"], "three", "three"),
            "two",
        )
        self.assertIsNone(fallback(["one"], "one", "one"))
        self.assertIsNone(
            fallback(["one", "two"], "two", "one")
        )

    def test_unstar_selected_entry_hands_off_without_marking_read(self) -> None:
        service = MockArticleService()
        for article in service.list_articles():
            service.set_starred(article.id, True)
        read_state = InMemoryReadStateStore()
        window = MainWindow(service, read_state_store=read_state)

        window.sidebar.select_feed(STARRED_FEED_ID)
        window.article_list.select_article("pyside-layout")
        self.assertTrue(read_state.is_read("pyside-layout"))

        window._set_starred_state("pyside-layout", False)

        self.assertEqual(
            window.article_list.current_article_id(),
            "local-first",
        )
        self.assertEqual(
            window.article_reader.current_article_id,
            "local-first",
        )
        self.assertFalse(read_state.is_read("local-first"))
        self.assertEqual(service.count_starred_articles(), 2)
        starred_item = next(
            window.sidebar.feed_list.item(row)
            for row in range(window.sidebar.feed_list.count())
            if window.sidebar.feed_list.item(row).data(FEED_ID_ROLE)
            == STARRED_FEED_ID
        )
        self.assertIn("2", starred_item.text())
        window.close()
        window.deleteLater()
        self.app.setStyleSheet("")

    def test_starred_view_composes_with_unread_filter(self) -> None:
        service = MockArticleService()
        for article in service.list_articles():
            service.set_starred(article.id, True)
        read_state = InMemoryReadStateStore({"mercury-start"})
        window = MainWindow(service, read_state_store=read_state)

        window.sidebar.select_feed(STARRED_FEED_ID)
        window.article_list.unread_filter_button.setChecked(True)

        self.assertEqual(
            window.article_list.visible_article_ids(),
            ["pyside-layout", "local-first"],
        )
        window.close()
        window.deleteLater()
        self.app.setStyleSheet("")


if __name__ == "__main__":
    unittest.main()
