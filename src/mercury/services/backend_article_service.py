from __future__ import annotations

from html import escape
from urllib.parse import urlparse

from core.database import DBManager
from domain.feed.opml_parser import import_opml as import_opml_file
from domain.feed.use_cases import FeedUseCase

from mercury.models.article import Article, Feed


class BackendArticleService:
    """Adapter from Member A's backend use cases to Member B's UI service."""

    def __init__(self, db: DBManager, feed_use_case: FeedUseCase) -> None:
        self._db = db
        self._feed_use_case = feed_use_case

    def list_feeds(self) -> list[Feed]:
        return [
            Feed(id=str(feed_id), title=title or xml_url)
            for feed_id, title, xml_url in self._db.get_all_feeds()
        ]

    def list_articles(self, feed_id: str | None = None) -> list[Article]:
        if feed_id is not None:
            return self._list_articles_for_feed(feed_id)

        articles: list[Article] = []
        for feed in self.list_feeds():
            articles.extend(self._list_articles_for_feed(feed.id, feed.title))
        return articles

    def get_article(self, article_id: str) -> Article | None:
        detail = self._db.get_article_detail(int(article_id))

        if detail is None:
            return None

        stored_title, description, stored_link = detail
        feed_id, source_title = self._find_feed_for_article(article_id)
        title, link = self._normalise_title_and_link(stored_title, stored_link)
        content_html = self._detail_html(description, link)

        return Article(
            id=str(article_id),
            feed_id=feed_id,
            title=title,
            source_title=source_title,
            content_html=content_html,
        )

    def add_feed(self, xml_url: str) -> str:
        before_count = len(self._db.get_all_feeds())
        self._feed_use_case.add_single_feed(xml_url)
        after_count = len(self._db.get_all_feeds())

        if after_count > before_count:
            return "Feed added and refreshed."

        return "Feed add request finished. It may already exist or failed validation."

    def import_opml(self, file_path: str) -> str:
        before_count = len(self._db.get_all_feeds())
        import_opml_file(self._feed_use_case, file_path)
        imported_count = len(self._db.get_all_feeds()) - before_count

        return f"OPML import finished. {max(imported_count, 0)} new feeds added."

    def refresh_all(self) -> str:
        self._feed_use_case.refresh_all()
        return "All feeds refreshed."

    def _list_articles_for_feed(
        self,
        feed_id: str,
        source_title: str | None = None,
    ) -> list[Article]:
        feed_id_int = int(feed_id)

        if source_title is None:
            source_title = self._feed_title(feed_id)

        articles: list[Article] = []
        for article_id, stored_title, published in self._db.get_articles_by_feed(feed_id_int):
            detail = self._db.get_article_detail(article_id)
            stored_link = detail[2] if detail is not None else ""
            title, _link = self._normalise_title_and_link(stored_title, stored_link)
            meta = escape(published or "")
            articles.append(
                Article(
                    id=str(article_id),
                    feed_id=str(feed_id),
                    title=title,
                    source_title=source_title or "",
                    content_html=f"<p>{meta}</p>" if meta else "",
                )
            )

        return articles

    def _feed_title(self, feed_id: str) -> str:
        for current_id, title, xml_url in self._db.get_all_feeds():
            if str(current_id) == str(feed_id):
                return title or xml_url

        return ""

    def _find_feed_for_article(self, article_id: str) -> tuple[str, str]:
        for feed in self.list_feeds():
            for current_article in self._db.get_articles_by_feed(int(feed.id)):
                if str(current_article[0]) == str(article_id):
                    return feed.id, feed.title

        return "", ""

    def _normalise_title_and_link(self, title: str | None, link: str | None) -> tuple[str, str]:
        safe_title = title or "Untitled"
        safe_link = link or ""

        if self._looks_like_url(safe_title) and safe_link and not self._looks_like_url(safe_link):
            return safe_link, safe_title

        return safe_title, safe_link

    def _detail_html(self, description: str | None, link: str) -> str:
        description_html = description or ""

        if link:
            safe_link = escape(link, quote=True)
            return (
                f"{description_html}"
                f"<p><a href=\"{safe_link}\">{safe_link}</a></p>"
            )

        return description_html or "<p>No article summary is available.</p>"

    def _looks_like_url(self, value: str) -> bool:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
