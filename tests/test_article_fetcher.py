import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.database import DBManager
from domain.feed.use_cases import FeedUseCase
from mercury.services.article_fetcher import ArticleFetcher, FetchResult
from mercury.services.backend_article_service import BackendArticleService


class ArticleFetcherTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fetcher = ArticleFetcher()

    def test_fetch_empty_url(self) -> None:
        result = self.fetcher.fetch("")
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "URL is empty")

    def test_fetch_success(self) -> None:
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.encoding = "utf-8"
        mock_response.content = b"<html><body>Test</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.Session.get", return_value=mock_response):
            result = self.fetcher.fetch("https://example.com/article")

        self.assertTrue(result.success)
        self.assertIn("<html><body>Test</body></html>", result.content)

    def test_fetch_http_error(self) -> None:
        import requests
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error: Not Found for url: https://example.com/not_found")

        with patch("requests.Session.get", return_value=mock_response):
            result = self.fetcher.fetch("https://example.com/not_found")

        self.assertFalse(result.success)
        self.assertIn("HTTP error", result.error_message)

    def test_fetch_timeout(self) -> None:
        with patch("requests.Session.get", side_effect=Exception("timed out")):
            with patch("requests.exceptions.Timeout", Exception):
                result = self.fetcher.fetch("https://example.com/slow")

        self.assertFalse(result.success)
        self.assertIn("timed out", result.error_message)

    def test_fetch_connection_error(self) -> None:
        with patch("requests.Session.get", side_effect=Exception("connection failed")):
            with patch("requests.exceptions.ConnectionError", Exception):
                result = self.fetcher.fetch("https://example.com/unreachable")

        self.assertFalse(result.success)
        self.assertIn("Connection failed", result.error_message)

    def test_decode_content_gbk(self) -> None:
        mock_response = MagicMock()
        mock_response.text = ""
        mock_response.encoding = None
        mock_response.content = "测试内容".encode("gbk")

        with patch("requests.Session.get", return_value=mock_response):
            result = self.fetcher.fetch("https://example.com/gbk")

        self.assertTrue(result.success)
        self.assertIn("测试内容", result.content)

    def test_fetch_result_dataclass(self) -> None:
        result = FetchResult(success=True, content="test content")
        self.assertTrue(result.success)
        self.assertEqual(result.content, "test content")
        self.assertIsNone(result.error_message)

        result_fail = FetchResult(success=False, error_message="failed")
        self.assertFalse(result_fail.success)
        self.assertEqual(result_fail.error_message, "failed")


class BackendArticleFetchTest(unittest.TestCase):
    def setUp(self) -> None:
        self.db = DBManager(":memory:")
        self.service = BackendArticleService(self.db, FeedUseCase(self.db))

    def tearDown(self) -> None:
        self.db.conn.close()

    def test_fetch_article_content_not_found(self) -> None:
        result = self.service.fetch_article_content("999")
        self.assertEqual(result, "Article not found.")

    def test_fetch_article_content_no_link(self) -> None:
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
        result = self.service.fetch_article_content(articles[0].id)
        self.assertEqual(result, "Article has no link.")

    def test_fetch_article_content_success(self) -> None:
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

        mock_response = MagicMock()
        mock_response.text = "<html><body>Fetched content</body></html>"
        mock_response.encoding = "utf-8"
        mock_response.content = b"<html><body>Fetched content</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.Session.get", return_value=mock_response):
            result = self.service.fetch_article_content(article_id)

        self.assertEqual(result, "Article content fetched successfully.")

        article = self.service.get_article(article_id)
        self.assertIsNotNone(article)
        self.assertEqual(article.fetch_status, "success")
        self.assertIn("Fetched content", article.original_html)
        self.assertIsNotNone(article.fetched_at)
        self.assertIsNone(article.fetch_error)

    def test_fetch_article_content_failure(self) -> None:
        feed_id = self.db.add_feed("Example", "https://example.com/rss")
        self.db.save_articles(
            feed_id,
            [
                {
                    "title": "Test Article",
                    "link": "https://example.com/fail",
                    "summary": "<p>Summary</p>",
                    "published": "Today",
                }
            ],
        )
        articles = self.service.list_articles(str(feed_id))
        article_id = articles[0].id

        with patch("requests.Session.get", side_effect=Exception("Connection failed")):
            with patch("requests.exceptions.ConnectionError", Exception):
                result = self.service.fetch_article_content(article_id)

        self.assertIn("Failed to fetch article content", result)

        article = self.service.get_article(article_id)
        self.assertIsNotNone(article)
        self.assertEqual(article.fetch_status, "failed")
        self.assertIsNotNone(article.fetch_error)

    def test_fetch_article_content_already_fetched(self) -> None:
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

        mock_response = MagicMock()
        mock_response.text = "<html><body>Fetched content</body></html>"
        mock_response.encoding = "utf-8"
        mock_response.content = b"<html><body>Fetched content</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.Session.get", return_value=mock_response):
            self.service.fetch_article_content(article_id)

        result = self.service.fetch_article_content(article_id)
        self.assertEqual(result, "Article content already fetched.")

    def test_fetch_article_content_force_refetch(self) -> None:
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

        mock_response = MagicMock()
        mock_response.text = "<html><body>Fetched content</body></html>"
        mock_response.encoding = "utf-8"
        mock_response.content = b"<html><body>Fetched content</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.Session.get", return_value=mock_response):
            self.service.fetch_article_content(article_id)

        with patch("requests.Session.get", return_value=mock_response):
            result = self.service.fetch_article_content(article_id, force=True)

        self.assertEqual(result, "Article content fetched successfully.")


if __name__ == "__main__":
    unittest.main()
