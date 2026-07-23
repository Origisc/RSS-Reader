from __future__ import annotations

from datetime import datetime
from html import escape
from urllib.parse import urlparse

from core.database import DBManager
from domain.feed.opml_parser import import_opml as import_opml_file
from domain.feed.use_cases import FeedUseCase

from mercury.models.article import Article, Feed
from mercury.services.article_fetcher import ArticleFetcher
from mercury.services.markdown_converter import MarkdownConverter
from mercury.services.reader_cleaner import ReaderCleaner
from mercury.services.translation_service import TranslationService


class FeedDeletionError(RuntimeError):
    """A deletion failure that the UI can present without database details."""


class BackendArticleService:
    """Adapter from Member A's backend use cases to Member B's UI service."""

    def __init__(
        self,
        db: DBManager,
        feed_use_case: FeedUseCase,
        translation_service: TranslationService | None = None,
    ) -> None:
        self._db = db
        self._feed_use_case = feed_use_case
        self._fetcher = ArticleFetcher()
        self._cleaner = ReaderCleaner()
        self._converter = MarkdownConverter()
        self._translator = translation_service

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
        detail = self._db.get_article_full_detail(int(article_id))

        if detail is None:
            return None

        (
            stored_title,
            description,
            stored_link,
            original_html,
            fetched_at,
            fetch_status,
            fetch_error,
            cleaned_html,
            cleaned_markdown,
            cleaned_at,
            clean_status,
            clean_error,
            translated_text,
            translated_at,
            translate_status,
            translate_error,
            target_language,
        ) = detail
        feed_id, source_title = self._find_feed_for_article(article_id)
        title, link = self._normalise_title_and_link(stored_title, stored_link)
        content_html = self._detail_html(description, link)

        return Article(
            id=str(article_id),
            feed_id=feed_id,
            title=title,
            source_title=source_title,
            content_html=content_html,
            original_html=original_html or "",
            fetched_at=fetched_at,
            fetch_status=fetch_status or "pending",
            fetch_error=fetch_error,
            cleaned_html=cleaned_html or "",
            cleaned_markdown=cleaned_markdown or "",
            cleaned_at=cleaned_at,
            clean_status=clean_status or "pending",
            clean_error=clean_error,
            translated_text=translated_text or "",
            translated_at=translated_at,
            translate_status=translate_status or "pending",
            translate_error=translate_error,
            target_language=target_language or "zh",
        )

    def fetch_article_content(self, article_id: str, force: bool = False) -> str:
        article = self.get_article(article_id)
        if article is None:
            return "Article not found."

        if not force and article.fetch_status == "success":
            return "Article content already fetched."

        detail = self._db.get_article_detail(int(article_id))
        if detail is None:
            return "Article detail not found."

        _, _, link = detail
        if not link:
            return "Article has no link."

        result = self._fetcher.fetch(link)
        fetched_at = self._fetcher.get_current_time()

        if result.success:
            self._db.save_article_html(
                int(article_id),
                result.content,
                fetched_at,
                status="success",
                error=None,
            )
            return "Article content fetched successfully."
        else:
            self._db.save_article_html(
                int(article_id),
                "",
                fetched_at,
                status="failed",
                error=result.error_message,
            )
            return f"Failed to fetch article content: {result.error_message}"

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

    def delete_feed(self, feed_id: str) -> None:
        try:
            feed_id_int = int(feed_id)
        except (TypeError, ValueError) as exc:
            raise FeedDeletionError("Invalid feed identifier.") from exc

        result = self._feed_use_case.remove_feed_by_id(feed_id_int)

        if result.get("success"):
            return

        raise FeedDeletionError(
            str(result.get("message") or "Feed deletion failed.")
        )

    def clean_article_content(self, article_id: str, force: bool = False) -> str:
        article = self.get_article(article_id)
        if article is None:
            return "Article not found."

        if not force and article.clean_status == "success":
            return "Article content already cleaned."

        if not article.original_html:
            detail = self._db.get_article_detail(int(article_id))
            has_link = detail is not None and detail[2]
            if has_link and article.fetch_status != "success":
                self.fetch_article_content(article_id)
                article = self.get_article(article_id)
                if article is None or article.fetch_status != "success":
                    return "Cannot clean: article fetch failed."
            if not article.original_html:
                return "Article has no original HTML content."

        result = self._cleaner.clean(article.original_html)
        cleaned_at = datetime.now().isoformat()

        if result.success:
            markdown_result = self._converter.convert(result.cleaned_html)
            cleaned_markdown = markdown_result.markdown if markdown_result.success else ""

            self._db.save_article_cleaned(
                int(article_id),
                result.cleaned_html,
                cleaned_markdown,
                cleaned_at,
                status="success",
                error=None,
            )
            return "Article content cleaned successfully."
        else:
            self._db.save_article_cleaned(
                int(article_id),
                "",
                "",
                cleaned_at,
                status="failed",
                error=result.error_message,
            )
            return f"Failed to clean article content: {result.error_message}"

    def convert_to_markdown(self, article_id: str, force: bool = False) -> str:
        article = self.get_article(article_id)
        if article is None:
            return "Article not found."

        if not force and article.cleaned_markdown:
            return "Article content already converted to Markdown."

        if not article.original_html:
            detail = self._db.get_article_detail(int(article_id))
            has_link = detail is not None and detail[2]
            if has_link and article.fetch_status != "success":
                self.fetch_article_content(article_id)
                article = self.get_article(article_id)
                if article is None or article.fetch_status != "success":
                    return "Cannot convert: article fetch failed."
            if not article.original_html:
                return "Article has no HTML content to convert."

        html_source = article.cleaned_html
        needs_clean = False

        if not html_source or article.clean_status != "success":
            clean_result = self._cleaner.clean(article.original_html)
            if clean_result.success:
                html_source = clean_result.cleaned_html
                needs_clean = True
            else:
                html_source = article.original_html

        result = self._converter.convert(html_source)
        cleaned_at = datetime.now().isoformat()

        if result.success:
            final_cleaned_html = html_source if needs_clean else article.cleaned_html
            self._db.save_article_cleaned(
                int(article_id),
                final_cleaned_html,
                result.markdown,
                cleaned_at,
                status="success",
                error=None,
            )
            return "Article content converted to Markdown successfully."
        else:
            self._db.save_article_cleaned(
                int(article_id),
                article.cleaned_html,
                "",
                cleaned_at,
                status="failed",
                error=result.error_message,
            )
            return f"Failed to convert article content: {result.error_message}"

    def translate_article_content(
        self,
        article_id: str,
        target_language: str = "zh",
        force: bool = False,
    ) -> str:
        article = self.get_article(article_id)
        if article is None:
            return "Article not found."

        if not force and article.translate_status == "success":
            return "Article content already translated."

        if self._translator is None:
            return "Translation service is not configured."

        if (
            not article.cleaned_markdown
            and not article.cleaned_html
            and not article.original_html
        ):
            detail = self._db.get_article_detail(int(article_id))
            has_link = detail is not None and detail[2]
            if has_link and article.fetch_status != "success":
                self.fetch_article_content(article_id)
                article = self.get_article(article_id)
                if article is None or article.fetch_status != "success":
                    return "Cannot translate: article fetch failed."

            if article.clean_status != "success":
                clean_result = self.clean_article_content(article_id)
                if "successfully" not in clean_result:
                    return f"Cannot translate: {clean_result}"
                article = self.get_article(article_id)

        text_source = article.cleaned_markdown or article.cleaned_html or article.original_html

        if not text_source:
            return "Article has no content to translate."

        result = self._translator.translate(text_source, target_language)
        translated_at = datetime.now().isoformat()

        if result.success:
            self._db.save_article_translated(
                int(article_id),
                result.translated_text,
                translated_at,
                target_language,
                status="success",
                error=None,
            )
            return f"Article content translated to {target_language} successfully."
        else:
            self._db.save_article_translated(
                int(article_id),
                "",
                translated_at,
                target_language,
                status="failed",
                error=result.error_message,
            )
            return f"Failed to translate article content: {result.error_message}"

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

    def _normalise_title_and_link(
        self,
        title: str | None,
        link: str | None,
    ) -> tuple[str, str]:
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
