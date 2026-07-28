import os
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from mercury.models.article import Article, Feed
from mercury.ui.main_window import MainWindow
from mercury.ui.sidebar import FEED_ID_ROLE, IS_VIRTUAL_ROLE


class MutableArticleService:
    def __init__(self) -> None:
        self.feeds = [
            Feed(id="feed-1", title="First feed"),
            Feed(id="feed-2", title="Second feed"),
        ]
        self.articles = [
            Article(
                id="article-1",
                feed_id="feed-1",
                title="First article",
                source_title="First feed",
                content_html="<p>First</p>",
            ),
            Article(
                id="article-2",
                feed_id="feed-2",
                title="Second article",
                source_title="Second feed",
                content_html="<p>Second</p>",
            ),
        ]

    def list_feeds(self) -> list[Feed]:
        return list(self.feeds)

    def list_articles(self, feed_id: str | None = None) -> list[Article]:
        if feed_id is None:
            return list(self.articles)

        return [article for article in self.articles if article.feed_id == feed_id]

    def get_article(self, article_id: str) -> Article | None:
        return next(
            (article for article in self.articles if article.id == article_id),
            None,
        )

    def set_starred(self, article_id: str, is_starred: bool) -> None:
        self.articles = [
            (
                replace(article, is_starred=is_starred)
                if article.id == article_id
                else article
            )
            for article in self.articles
        ]

    def list_starred_articles(self) -> list[Article]:
        return [
            article for article in self.articles if article.is_starred
        ]

    def count_starred_articles(self) -> int:
        return sum(article.is_starred for article in self.articles)

    def fetch_article_content(
        self,
        article_id: str,
        force: bool = False,
    ) -> str:
        return f"Fetched {article_id}, force={force}"

    def clean_article_content(
        self,
        article_id: str,
        force: bool = False,
    ) -> str:
        return f"Cleaned {article_id}, force={force}"

    def convert_to_markdown(
        self,
        article_id: str,
        force: bool = False,
    ) -> str:
        return f"Converted {article_id}, force={force}"

    def translate_article_content(
        self,
        article_id: str,
        target_language: str = "zh",
        force: bool = False,
    ) -> str:
        return (
            f"Translated {article_id} to {target_language}, "
            f"force={force}"
        )

    def add_feed(self, xml_url: str) -> str:
        return f"Added {xml_url}"

    def import_opml(self, file_path: str) -> str:
        return f"Imported {file_path}"

    def refresh_all(self) -> str:
        return "Refreshed"


class FakeFeedDeletionService:
    def __init__(self, article_service: MutableArticleService) -> None:
        self.article_service = article_service
        self.deleted_feed_ids: list[str] = []
        self.deleted_batches: list[tuple[str, ...]] = []

    def delete_feed(self, feed_id: str) -> None:
        self.deleted_feed_ids.append(feed_id)
        self.article_service.feeds = [
            feed for feed in self.article_service.feeds if feed.id != feed_id
        ]
        self.article_service.articles = [
            article
            for article in self.article_service.articles
            if article.feed_id != feed_id
        ]

    def delete_feeds(self, feed_ids) -> None:
        selected_ids = tuple(dict.fromkeys(str(feed_id) for feed_id in feed_ids))
        existing_ids = {feed.id for feed in self.article_service.feeds}
        if not selected_ids or not set(selected_ids).issubset(existing_ids):
            raise RuntimeError("invalid batch")

        self.deleted_batches.append(selected_ids)
        self.article_service.feeds = [
            feed
            for feed in self.article_service.feeds
            if feed.id not in selected_ids
        ]
        self.article_service.articles = [
            article
            for article in self.article_service.articles
            if article.feed_id not in selected_ids
        ]


class FailingFeedDeletionService:
    def delete_feed(self, feed_id: str) -> None:
        raise RuntimeError("backend detail should not leak")


class FeedDeletionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.article_service = MutableArticleService()
        self.deletion_service = FakeFeedDeletionService(self.article_service)
        self.window = MainWindow(
            self.article_service,
            feed_deletion_service=self.deletion_service,
        )

    def tearDown(self) -> None:
        self.window.close()
        self.window.deleteLater()
        self.app.setStyleSheet("")

    def test_cancel_keeps_feed_and_cached_articles(self) -> None:
        with patch.object(
            self.window,
            "_confirm_feed_deletion",
            return_value=False,
        ):
            self.window._delete_feed("feed-1")

        self.assertEqual(self.deletion_service.deleted_feed_ids, [])
        self.assertEqual(len(self.article_service.list_feeds()), 2)
        self.assertEqual(len(self.article_service.list_articles()), 2)

    def test_confirmation_uses_cancel_as_default_and_escape_action(self) -> None:
        dialog_state: list[tuple[str, bool]] = []

        def cancel_dialog() -> None:
            dialog = QApplication.activeModalWidget()
            self.assertIsInstance(dialog, QMessageBox)
            dialog_state.append(
                (
                    dialog.defaultButton().text(),
                    dialog.defaultButton() is dialog.escapeButton(),
                )
            )
            dialog.defaultButton().click()

        QTimer.singleShot(0, cancel_dialog)

        self.assertFalse(self.window._confirm_feed_deletion("First feed"))
        self.assertEqual(dialog_state, [("取消", True)])

    def test_batch_confirmation_lists_scope_and_defaults_to_cancel(
        self,
    ) -> None:
        dialog_state: list[tuple[str, bool, str]] = []

        def cancel_dialog() -> None:
            dialog = QApplication.activeModalWidget()
            self.assertIsInstance(dialog, QMessageBox)
            dialog_state.append(
                (
                    dialog.defaultButton().text(),
                    dialog.defaultButton() is dialog.escapeButton(),
                    dialog.text(),
                )
            )
            dialog.defaultButton().click()

        QTimer.singleShot(0, cancel_dialog)

        self.assertFalse(
            self.window._confirm_feeds_deletion(
                self.article_service.list_feeds()
            )
        )
        self.assertEqual(dialog_state[0][0:2], ("取消", True))
        self.assertIn("2", dialog_state[0][2])
        self.assertIn("First feed", dialog_state[0][2])
        self.assertIn("Second feed", dialog_state[0][2])

    def test_confirmed_deletion_refreshes_feed_entries_and_reader(self) -> None:
        self.window._show_article("article-1")

        with patch.object(
            self.window,
            "_confirm_feed_deletion",
            return_value=True,
        ):
            self.window._delete_feed("feed-1")

        self.assertEqual(self.deletion_service.deleted_feed_ids, ["feed-1"])
        self.assertEqual(
            [feed.id for feed in self.article_service.list_feeds()],
            ["feed-2"],
        )
        self.assertEqual(
            [article.id for article in self.article_service.list_articles()],
            ["article-2"],
        )
        real_feed_items = [
            self.window.sidebar.feed_list.item(row)
            for row in range(self.window.sidebar.feed_list.count())
            if not bool(
                self.window.sidebar.feed_list.item(row).data(
                    IS_VIRTUAL_ROLE
                )
            )
        ]
        self.assertEqual(len(real_feed_items), 1)
        self.assertEqual(
            real_feed_items[0].data(FEED_ID_ROLE),
            "feed-2",
        )
        self.assertEqual(self.window.article_list.list_widget.count(), 1)
        self.assertIsNone(self.window.article_reader.current_article_id)
        self.assertIn("First feed", self.window.statusBar().currentMessage())

    def test_confirmed_batch_deletion_refreshes_all_views(self) -> None:
        self.window._show_article("article-1")
        self.window.sidebar.batch_delete_button.click()
        for row in range(self.window.sidebar.feed_list.count()):
            item = self.window.sidebar.feed_list.item(row)
            if item.data(FEED_ID_ROLE) in {"feed-1", "feed-2"}:
                item.setSelected(True)

        with patch.object(
            self.window,
            "_confirm_feeds_deletion",
            return_value=True,
        ):
            self.window.sidebar.batch_delete_button.click()

        self.assertEqual(
            self.deletion_service.deleted_batches,
            [("feed-1", "feed-2")],
        )
        self.assertEqual(self.article_service.list_feeds(), [])
        self.assertEqual(self.article_service.list_articles(), [])
        self.assertEqual(self.window.article_list.list_widget.count(), 0)
        self.assertIsNone(self.window.article_reader.current_article_id)
        self.assertIn("2", self.window.statusBar().currentMessage())
        self.assertEqual(
            self.window.sidebar.feed_list.selectionMode().name,
            "SingleSelection",
        )
        self.assertEqual(
            self.window.sidebar.batch_delete_button.text(),
            "多选删除",
        )

    def test_missing_adapter_explains_that_nothing_was_deleted(self) -> None:
        self.window.close()
        self.window.deleteLater()
        self.window = MainWindow(self.article_service)

        with patch.object(QMessageBox, "information") as information:
            self.window._delete_feed("feed-1")

        information.assert_called_once()
        self.assertIn("删除服务未配置", information.call_args.args[2])
        self.assertEqual(len(self.article_service.list_feeds()), 2)
        self.assertEqual(len(self.article_service.list_articles()), 2)

    def test_adapter_failure_is_translated_and_keeps_current_data(self) -> None:
        self.window.close()
        self.window.deleteLater()
        self.window = MainWindow(
            self.article_service,
            feed_deletion_service=FailingFeedDeletionService(),
        )

        with (
            patch.object(
                self.window,
                "_confirm_feed_deletion",
                return_value=True,
            ),
            patch.object(QMessageBox, "warning") as warning,
        ):
            self.window._delete_feed("feed-1")

        warning.assert_called_once()
        self.assertIn("删除失败", warning.call_args.args[2])
        self.assertNotIn("backend detail", warning.call_args.args[2])
        self.assertEqual(len(self.article_service.list_feeds()), 2)
        self.assertEqual(len(self.article_service.list_articles()), 2)


if __name__ == "__main__":
    unittest.main()
