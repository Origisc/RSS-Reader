import sys
import tempfile
import unittest
from contextlib import chdir
from pathlib import Path
from unittest.mock import Mock, patch

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.database import DBManager
from domain.feed.import_errors import (
    FeedImportError,
    FeedImportErrorCode,
)
from domain.feed.use_cases import FeedUseCase
from mercury.services.backend_article_service import BackendArticleService


RSS_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Local Test Feed</title>
    <link>https://example.com/</link>
    <description>Local fixture</description>
    <item>
      <title>Local article</title>
      <link>https://example.com/article</link>
      <description>Readable content</description>
    </item>
  </channel>
</rss>
"""


def write_feed(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(RSS_CONTENT, encoding="utf-8")
    return path


def write_opml(path: Path, xml_url: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<opml version="2.0">\n'
            "  <body>\n"
            f'    <outline text="Local Feed" xmlUrl="{xml_url}" />\n'
            "  </body>\n"
            "</opml>\n"
        ),
        encoding="utf-8",
    )
    return path


class FeedImportPathTest(unittest.TestCase):
    def setUp(self) -> None:
        self.db = DBManager(":memory:")
        self.use_case = FeedUseCase(self.db)
        self.service = BackendArticleService(self.db, self.use_case)

    def tearDown(self) -> None:
        self.db.conn.close()

    def test_add_feed_accepts_absolute_local_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            feed_path = write_feed(Path(temp_dir) / "absolute.xml")

            message = self.service.add_feed(str(feed_path))

            stored_feed = self.db.get_all_feeds()[0]
            self.assertEqual(stored_feed[1], "Local Test Feed")
            self.assertEqual(stored_feed[2], str(feed_path.resolve()))
            self.assertIn("Feed added", message)
            self.assertEqual(
                len(self.db.get_articles_by_feed(stored_feed[0])),
                1,
            )

    def test_add_feed_accepts_path_relative_to_working_directory(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            feed_path = write_feed(root / "fixtures" / "relative.xml")

            with chdir(root):
                message = self.service.add_feed(
                    "fixtures/relative.xml"
                )

            stored_feed = self.db.get_all_feeds()[0]
            self.assertEqual(stored_feed[2], str(feed_path.resolve()))
            self.assertIn("Feed added", message)

    def test_http_feed_remains_supported_without_real_network(self) -> None:
        response = Mock()
        response.content = RSS_CONTENT.encode("utf-8")
        response.raise_for_status.return_value = None

        with patch(
            "domain.feed.use_cases.requests.get",
            return_value=response,
        ) as get:
            message = self.service.add_feed(
                "https://example.com/feed.xml"
            )

        get.assert_called_once_with(
            "https://example.com/feed.xml",
            timeout=10,
        )
        self.assertIn("Feed added", message)
        self.assertEqual(
            self.db.get_all_feeds()[0][2],
            "https://example.com/feed.xml",
        )

    def test_opml_accepts_relative_path_and_resolves_relative_feed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            feed_path = write_feed(
                root / "subscriptions" / "feeds" / "local.xml"
            )
            write_opml(
                root / "subscriptions" / "feeds.opml",
                "feeds/local.xml",
            )

            with chdir(root):
                message = self.service.import_opml(
                    "subscriptions/feeds.opml"
                )

            stored_feed = self.db.get_all_feeds()[0]
            self.assertEqual(stored_feed[2], str(feed_path.resolve()))
            self.assertIn("1 new feeds", message)

    def test_opml_accepts_absolute_opml_and_feed_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            feed_path = write_feed(root / "absolute-feed.xml")
            opml_path = write_opml(
                root / "absolute.opml",
                str(feed_path),
            )

            message = self.service.import_opml(str(opml_path))

            self.assertEqual(
                self.db.get_all_feeds()[0][2],
                str(feed_path.resolve()),
            )
            self.assertIn("1 new feeds", message)

    def test_missing_local_feed_reports_resolved_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with chdir(root):
                with self.assertRaises(FeedImportError) as context:
                    self.service.add_feed("missing.xml")

            self.assertEqual(
                context.exception.code,
                FeedImportErrorCode.FILE_NOT_FOUND,
            )
            self.assertEqual(
                context.exception.source,
                str((root / "missing.xml").resolve()),
            )
            self.assertIn("not found", str(context.exception))

    def test_invalid_local_feed_reports_invalid_feed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            feed_path = Path(temp_dir) / "invalid.xml"
            feed_path.write_text("<not-a-feed />", encoding="utf-8")

            with self.assertRaises(FeedImportError) as context:
                self.service.add_feed(str(feed_path))

            self.assertEqual(
                context.exception.code,
                FeedImportErrorCode.INVALID_FEED,
            )
            self.assertEqual(
                context.exception.source,
                str(feed_path.resolve()),
            )

    def test_directory_and_unsupported_scheme_have_clear_errors(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(FeedImportError) as directory_context:
                self.service.add_feed(temp_dir)
            with self.assertRaises(FeedImportError) as scheme_context:
                self.service.add_feed("ftp://example.com/feed.xml")

        self.assertEqual(
            directory_context.exception.code,
            FeedImportErrorCode.NOT_A_FILE,
        )
        self.assertEqual(
            scheme_context.exception.code,
            FeedImportErrorCode.UNSUPPORTED_SCHEME,
        )

    def test_http_failure_reports_source_and_reason(self) -> None:
        with patch(
            "domain.feed.use_cases.requests.get",
            side_effect=requests.Timeout("offline fixture"),
        ):
            with self.assertRaises(FeedImportError) as context:
                self.service.add_feed("https://example.com/feed.xml")

        self.assertEqual(
            context.exception.code,
            FeedImportErrorCode.NETWORK_FAILED,
        )
        self.assertEqual(
            context.exception.source,
            "https://example.com/feed.xml",
        )
        self.assertIn("offline fixture", context.exception.detail)

    def test_missing_and_invalid_opml_have_distinct_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            missing_path = root / "missing.opml"
            invalid_path = root / "invalid.opml"
            invalid_path.write_text("<opml><body>", encoding="utf-8")

            with self.assertRaises(FeedImportError) as missing_context:
                self.service.import_opml(str(missing_path))
            with self.assertRaises(FeedImportError) as invalid_context:
                self.service.import_opml(str(invalid_path))

            self.assertEqual(
                missing_context.exception.code,
                FeedImportErrorCode.FILE_NOT_FOUND,
            )
            self.assertEqual(
                invalid_context.exception.code,
                FeedImportErrorCode.INVALID_OPML,
            )

    def test_opml_without_feed_outlines_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            opml_path = Path(temp_dir) / "empty.opml"
            opml_path.write_text(
                "<opml version='2.0'><body /></opml>",
                encoding="utf-8",
            )

            with self.assertRaises(FeedImportError) as context:
                self.service.import_opml(str(opml_path))

            self.assertEqual(
                context.exception.code,
                FeedImportErrorCode.OPML_NO_FEEDS,
            )

    def test_opml_rejects_invalid_local_feed_before_saving(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            invalid_feed = root / "invalid-feed.xml"
            invalid_feed.write_text("<not-a-feed />", encoding="utf-8")
            opml_path = write_opml(
                root / "invalid-feed.opml",
                "invalid-feed.xml",
            )

            with self.assertRaises(FeedImportError) as context:
                self.service.import_opml(str(opml_path))

            self.assertEqual(
                context.exception.code,
                FeedImportErrorCode.INVALID_FEED,
            )
            self.assertEqual(self.db.get_all_feeds(), [])

    def test_non_utf8_feed_has_clear_read_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            feed_path = Path(temp_dir) / "non-utf8.xml"
            feed_path.write_bytes(b"\xff\xfe\x00\x00")

            with self.assertRaises(FeedImportError) as context:
                self.service.add_feed(str(feed_path))

            self.assertEqual(
                context.exception.code,
                FeedImportErrorCode.FILE_READ_FAILED,
            )
            self.assertEqual(
                context.exception.source,
                str(feed_path.resolve()),
            )


if __name__ == "__main__":
    unittest.main()
