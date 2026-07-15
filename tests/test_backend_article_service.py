import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.database import DBManager
from domain.feed.use_cases import FeedUseCase
from mercury.services.backend_article_service import BackendArticleService


class BackendArticleServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.db = DBManager(":memory:")
        self.service = BackendArticleService(self.db, FeedUseCase(self.db))

    def test_lists_feeds_from_backend_database(self) -> None:
        self.db.add_feed("Example", "https://example.com/rss")

        feeds = self.service.list_feeds()

        self.assertEqual(len(feeds), 1)
        self.assertEqual(feeds[0].title, "Example")

    def test_lists_articles_and_corrects_swapped_title_link_rows(self) -> None:
        feed_id = self.db.add_feed("Example", "https://example.com/rss")
        self.db.save_articles(
            feed_id,
            [
                {
                    "title": "Readable title",
                    "link": "https://example.com/article",
                    "summary": "<p>Hello</p>",
                    "published": "Today",
                }
            ],
        )

        articles = self.service.list_articles(str(feed_id))
        detail = self.service.get_article(articles[0].id)

        self.assertEqual(articles[0].title, "Readable title")
        self.assertIsNotNone(detail)
        self.assertEqual(detail.title, "Readable title")
        self.assertIn("https://example.com/article", detail.content_html)

    def test_imports_opml_into_backend_database(self) -> None:
        opml_content = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <body>
    <outline text="Example Feed" xmlUrl="https://example.com/feed.xml" />
  </body>
</opml>
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            opml_path = Path(temp_dir) / "feeds.opml"
            opml_path.write_text(opml_content, encoding="utf-8")

            message = self.service.import_opml(str(opml_path))

        feeds = self.service.list_feeds()
        self.assertIn("1 new feeds", message)
        self.assertEqual(feeds[0].title, "Example Feed")


if __name__ == "__main__":
    unittest.main()
