import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtWidgets import QApplication

from core.database import DBManager
from domain.feed.use_cases import FeedUseCase
from mercury.services.backend_article_service import BackendArticleService
from mercury.ui.article_reader import ArticleReader
from mercury.ui.reader_document import ReaderDocument, ReaderView


def rss_document(title: str, entries: tuple[tuple[str, str], ...]) -> str:
    items = "".join(
        (
            "<item>"
            f"<title>{entry_title}</title>"
            f"<link>{link}</link>"
            f"<guid>{link}</guid>"
            "<description><![CDATA["
            f"<p>{entry_title} body</p>"
            "<ul><li>First point</li><li>Second point</li></ul>"
            "]]></description>"
            "</item>"
        )
        for entry_title, link in entries
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<rss version=\"2.0\"><channel>"
        f"<title>{title}</title>"
        "<link>https://example.com/</link>"
        f"{items}"
        "</channel></rss>"
    )


class CoreReadingAcceptanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.db = DBManager(str(self.root / "reader.db"))
        self.feed_use_case = FeedUseCase(self.db)
        self.service = BackendArticleService(
            self.db,
            self.feed_use_case,
        )

    def tearDown(self) -> None:
        self.db.conn.close()
        self.temp_dir.cleanup()

    def test_feed_opml_sync_and_reader_views_work_as_one_flow(self) -> None:
        primary_feed = self.root / "primary.xml"
        primary_feed.write_text(
            rss_document(
                "Primary Feed",
                (
                    ("Alpha", "https://example.com/alpha"),
                    ("Beta", "https://example.com/beta"),
                ),
            ),
            encoding="utf-8",
        )

        self.service.add_feed(str(primary_feed))
        self.assertEqual(len(self.service.list_feeds()), 1)
        self.assertEqual(len(self.service.list_articles()), 2)

        self.service.refresh_all()
        self.service.refresh_all()
        self.assertEqual(
            len(self.service.list_articles()),
            2,
            "Repeated sync must not duplicate existing entries.",
        )

        primary_feed.write_text(
            rss_document(
                "Primary Feed",
                (
                    ("Alpha", "https://example.com/alpha"),
                    ("Beta", "https://example.com/beta"),
                    ("Gamma", "https://example.com/gamma"),
                ),
            ),
            encoding="utf-8",
        )
        self.assertIn("All 1 feeds refreshed", self.service.refresh_all())
        self.assertEqual(len(self.service.list_articles()), 3)

        secondary_feed = self.root / "secondary.xml"
        secondary_feed.write_text(
            rss_document(
                "Secondary Feed",
                (("Delta", "https://example.com/delta"),),
            ),
            encoding="utf-8",
        )
        opml_path = self.root / "feeds.opml"
        opml_path.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head><title>Grouped feeds</title></head>
  <body>
    <outline text="Local group">
      <outline text="Secondary" xmlUrl="secondary.xml"/>
      <outline text="Duplicate" xmlUrl="secondary.xml"/>
    </outline>
  </body>
</opml>
""",
            encoding="utf-8",
        )

        self.assertIn("1 new feeds added", self.service.import_opml(str(opml_path)))
        self.assertEqual(len(self.service.list_feeds()), 2)
        self.assertEqual(
            len(self.service.list_articles()),
            4,
            "OPML import must make the first batch of entries immediately readable.",
        )

        article = next(
            article
            for article in self.service.list_articles()
            if article.title == "Alpha"
        )
        self.db.save_article_html(
            int(article.id),
            (
                "<html><body><article>"
                "<h2>Alpha reader heading</h2>"
                "<p>Readable cleaned paragraph.</p>"
                "<ul><li>First point</li><li>Second point</li></ul>"
                "</article></body></html>"
            ),
            "2026-07-29T12:00:00",
            status="success",
            error=None,
        )
        self.assertIn(
            "cleaned successfully",
            self.service.clean_article_content(article.id),
        )

        processed_article = self.service.get_article(article.id)
        self.assertIsNotNone(processed_article)
        document = ReaderDocument.from_article(processed_article)
        reader = ArticleReader()
        self.addCleanup(reader.deleteLater)
        reader.show_article(processed_article, document)

        reader.set_view(ReaderView.RAW)
        self.assertIn("Alpha body", reader.content.toPlainText())
        reader.set_view(ReaderView.CLEANED_HTML)
        self.assertIn("Readable cleaned paragraph", reader.content.toPlainText())
        reader.set_view(ReaderView.MARKDOWN)
        markdown_text = reader.content.toPlainText()
        self.assertIn("Alpha reader heading", markdown_text)
        self.assertIn("First point", markdown_text)

        primary_feed.unlink()
        sync_message = self.service.refresh_all()
        self.assertIn("Feed sync completed with errors", sync_message)
        self.assertIn(str(primary_feed.resolve()), sync_message)
        self.assertIn("1/2 succeeded", sync_message)


if __name__ == "__main__":
    unittest.main()
