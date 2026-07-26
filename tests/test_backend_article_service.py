import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.database import DBManager
from domain.feed.use_cases import FeedUseCase
from mercury.llm.provider import MockLLMProvider
from mercury.services.article_fetcher import FetchResult
from mercury.services.backend_article_service import (
    BackendArticleService,
    FeedDeletionError,
)
from mercury.services.translation_service import TranslationService


class BackendArticleServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.db = DBManager(":memory:")
        self.service = BackendArticleService(self.db, FeedUseCase(self.db))

    def tearDown(self) -> None:
        self.db.conn.close()

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

    def test_fetch_uses_url_from_legacy_swapped_title_link_row(self) -> None:
        feed_id = self.db.add_feed(
            "Legacy",
            "https://example.com/feed",
        )
        with self.db.conn:
            cursor = self.db.conn.execute(
                """
                INSERT INTO articles (
                    feed_id,
                    title,
                    link,
                    description,
                    fetch_status
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    feed_id,
                    "https://example.com/legacy",
                    "Readable legacy title",
                    "<p>Summary</p>",
                    "failed",
                ),
            )
            article_id = str(cursor.lastrowid)
        self.service._fetcher.fetch = Mock(
            return_value=FetchResult(
                success=True,
                content="<html><body>Fetched</body></html>",
            )
        )

        result = self.service.fetch_article_content(
            article_id,
            force=True,
        )

        self.assertEqual(
            result,
            "Article content fetched successfully.",
        )
        self.service._fetcher.fetch.assert_called_once_with(
            "https://example.com/legacy"
        )
        self.assertEqual(
            self.service.get_article(article_id).fetch_status,
            "success",
        )

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

    def test_deletes_feed_and_its_cached_articles(self) -> None:
        feed_id = self.db.add_feed("Example", "https://example.com/rss")
        self.db.save_articles(
            feed_id,
            [
                {
                    "title": "Cached article",
                    "link": "https://example.com/cached",
                    "summary": "Cached content",
                }
            ],
        )

        self.service.delete_feed(str(feed_id))

        self.assertEqual(self.db.get_all_feeds(), [])
        self.assertEqual(self.db.get_articles_by_feed(feed_id), [])

    def test_missing_feed_returns_adapter_error(self) -> None:
        with self.assertRaises(FeedDeletionError):
            self.service.delete_feed("999")

    def test_invalid_feed_id_never_reaches_database(self) -> None:
        with self.assertRaisesRegex(
            FeedDeletionError,
            "Invalid feed identifier",
        ):
            self.service.delete_feed("not-an-integer")

    def test_clean_article_content_success(self) -> None:
        feed_id = self.db.add_feed("Example", "https://example.com/rss")
        self.db.save_articles(
            feed_id,
            [
                {
                    "title": "Test Article",
                    "link": "https://example.com/article",
                    "summary": "<p>Summary</p>",
                    "published": "Today",
                }
            ],
        )
        articles = self.service.list_articles(str(feed_id))
        article_id = articles[0].id

        self.db.save_article_html(
            int(article_id),
            "<html><body><article><h1>Article Title</h1><p>Content</p></article></body></html>",
            "2024-01-01T00:00:00",
            status="success",
        )

        result = self.service.clean_article_content(article_id)

        self.assertEqual(result, "Article content cleaned successfully.")
        article = self.service.get_article(article_id)
        self.assertIsNotNone(article)
        self.assertEqual(article.clean_status, "success")
        self.assertIn("<h1>", article.cleaned_html)
        self.assertIn("Article Title", article.cleaned_html)
        self.assertIsNotNone(article.cleaned_at)

    def test_clean_article_content_already_cleaned(self) -> None:
        feed_id = self.db.add_feed("Example", "https://example.com/rss")
        self.db.save_articles(
            feed_id,
            [
                {
                    "title": "Test Article",
                    "link": "https://example.com/article",
                    "summary": "<p>Summary</p>",
                    "published": "Today",
                }
            ],
        )
        articles = self.service.list_articles(str(feed_id))
        article_id = articles[0].id

        self.db.save_article_html(
            int(article_id),
            "<html><body><p>Content</p></body></html>",
            "2024-01-01T00:00:00",
            status="success",
        )
        self.db.save_article_cleaned(
            int(article_id),
            "<p>Cleaned</p>",
            "",
            "2024-01-01T00:00:01",
            status="success",
        )

        result = self.service.clean_article_content(article_id)

        self.assertEqual(result, "Article content already cleaned.")

    def test_clean_article_content_force_reclean(self) -> None:
        feed_id = self.db.add_feed("Example", "https://example.com/rss")
        self.db.save_articles(
            feed_id,
            [
                {
                    "title": "Test Article",
                    "link": "https://example.com/article",
                    "summary": "<p>Summary</p>",
                    "published": "Today",
                }
            ],
        )
        articles = self.service.list_articles(str(feed_id))
        article_id = articles[0].id

        self.db.save_article_html(
            int(article_id),
            "<html><body><article><h1>New Title</h1><p>New Content</p></article></body></html>",
            "2024-01-01T00:00:00",
            status="success",
        )
        self.db.save_article_cleaned(
            int(article_id),
            "<p>Old Cleaned</p>",
            "",
            "2024-01-01T00:00:01",
            status="success",
        )

        result = self.service.clean_article_content(article_id, force=True)

        self.assertEqual(result, "Article content cleaned successfully.")
        article = self.service.get_article(article_id)
        self.assertIn("New Title", article.cleaned_html)

    def test_clean_article_content_no_html(self) -> None:
        feed_id = self.db.add_feed("Example", "https://example.com/rss")
        self.db.save_articles(
            feed_id,
            [
                {
                    "title": "Test Article",
                    "link": "",
                    "summary": "<p>Summary</p>",
                    "published": "Today",
                }
            ],
        )
        articles = self.service.list_articles(str(feed_id))
        article_id = articles[0].id

        result = self.service.clean_article_content(article_id)

        self.assertEqual(result, "Article has no original HTML content.")

    def test_convert_to_markdown_success(self) -> None:
        feed_id = self.db.add_feed("Example", "https://example.com/rss")
        self.db.save_articles(
            feed_id,
            [
                {
                    "title": "Test Article",
                    "link": "https://example.com/article",
                    "summary": "<p>Summary</p>",
                    "published": "Today",
                }
            ],
        )
        articles = self.service.list_articles(str(feed_id))
        article_id = articles[0].id

        self.db.save_article_html(
            int(article_id),
            "<html><body><article><h1>Article Title</h1><p>Content</p></article></body></html>",
            "2024-01-01T00:00:00",
            status="success",
        )

        result = self.service.convert_to_markdown(article_id)

        self.assertEqual(result, "Article content converted to Markdown successfully.")
        article = self.service.get_article(article_id)
        self.assertIsNotNone(article)
        self.assertIn("# Article Title", article.cleaned_markdown)
        self.assertIn("Content", article.cleaned_markdown)

    def test_convert_to_markdown_already_converted(self) -> None:
        feed_id = self.db.add_feed("Example", "https://example.com/rss")
        self.db.save_articles(
            feed_id,
            [
                {
                    "title": "Test Article",
                    "link": "https://example.com/article",
                    "summary": "<p>Summary</p>",
                    "published": "Today",
                }
            ],
        )
        articles = self.service.list_articles(str(feed_id))
        article_id = articles[0].id

        self.db.save_article_html(
            int(article_id),
            "<html><body><p>Content</p></body></html>",
            "2024-01-01T00:00:00",
            status="success",
        )
        self.db.save_article_cleaned(
            int(article_id),
            "<p>Cleaned</p>",
            "# Title\nContent",
            "2024-01-01T00:00:01",
            status="success",
        )

        result = self.service.convert_to_markdown(article_id)

        self.assertEqual(result, "Article content already converted to Markdown.")

    def test_translation_requires_injected_provider_service(self) -> None:
        feed_id = self.db.add_feed("Example", "https://example.com/rss")
        self.db.save_articles(
            feed_id,
            [
                {
                    "title": "Test Article",
                    "link": "",
                    "summary": "<p>Summary</p>",
                    "published": "Today",
                }
            ],
        )
        article_id = self.service.list_articles(str(feed_id))[0].id

        result = self.service.translate_article_content(article_id)

        self.assertEqual(result, "Translation service is not configured.")

    def test_translates_and_persists_cleaned_article_content(self) -> None:
        feed_id = self.db.add_feed("Example", "https://example.com/rss")
        self.db.save_articles(
            feed_id,
            [
                {
                    "title": "Test Article",
                    "link": "",
                    "summary": "<p>Summary</p>",
                    "published": "Today",
                }
            ],
        )
        article_id = self.service.list_articles(str(feed_id))[0].id
        self.db.save_article_cleaned(
            int(article_id),
            "<p>Cleaned source</p>",
            "Cleaned source",
            "2024-01-01T00:00:01",
            status="success",
        )
        provider = MockLLMProvider(response_text="已翻译正文")
        service = BackendArticleService(
            self.db,
            FeedUseCase(self.db),
            TranslationService(provider),
        )

        result = service.translate_article_content(article_id, "zh")
        article = service.get_article(article_id)

        self.assertIn("translated to zh successfully", result)
        self.assertIsNotNone(article)
        self.assertEqual(article.translated_text, "已翻译正文")
        self.assertEqual(article.translate_status, "success")
        self.assertEqual(article.target_language, "zh")


if __name__ == "__main__":
    unittest.main()
