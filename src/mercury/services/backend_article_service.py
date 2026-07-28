from __future__ import annotations

import sqlite3
from collections.abc import Collection
from datetime import datetime
from html import escape
from urllib.parse import urlparse

from core.database import DBManager
from domain.feed.opml_parser import import_opml as import_opml_file
from domain.feed.use_cases import FeedUseCase

from mercury.models.article import Article, Feed
from mercury.models.tag import Tag
from mercury.services.article_fetcher import ArticleFetcher
from mercury.services.article_service import StarredEntryError
from mercury.services.markdown_converter import MarkdownConverter
from mercury.services.reader_cleaner import ReaderCleaner
from mercury.services.tag_service import TagServiceError
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
            translated_title,
            is_starred,
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
            is_starred=bool(is_starred),
            translated_title=translated_title or "",
        )

    def set_starred(self, article_id: str, is_starred: bool) -> None:
        try:
            article_id_int = int(article_id)
        except (TypeError, ValueError) as exc:
            raise StarredEntryError("Invalid article identifier.") from exc

        if not self._db.set_article_starred(article_id_int, is_starred):
            raise StarredEntryError("Article not found.")

    def list_starred_articles(self) -> list[Article]:
        articles: list[Article] = []

        for (
            article_id,
            feed_id,
            stored_title,
            stored_link,
            published,
            is_starred,
            source_title,
            translated_title,
        ) in self._db.get_starred_articles():
            title, _link = self._normalise_title_and_link(
                stored_title,
                stored_link,
            )
            display_title = translated_title or title
            meta = escape(published or "")
            articles.append(
                Article(
                    id=str(article_id),
                    feed_id=str(feed_id),
                    title=display_title,
                    source_title=source_title or "",
                    content_html=f"<p>{meta}</p>" if meta else "",
                    is_starred=bool(is_starred),
                    translated_title=translated_title or "",
                )
            )

        return articles

    def count_starred_articles(self) -> int:
        return self._db.count_starred_articles()

    def list_tags(self) -> list[Tag]:
        return [
            Tag(
                id=str(tag_id),
                name=name,
                article_count=int(article_count),
            )
            for tag_id, name, article_count in self._db.list_tags()
        ]

    def list_article_tags(self, article_id: str) -> list[Tag]:
        article_id_int = self._tag_numeric_id(
            article_id,
            "article",
        )
        if self.get_article(article_id) is None:
            raise TagServiceError("Article not found.")

        return [
            Tag(id=str(tag_id), name=name)
            for tag_id, name in self._db.get_article_tags(article_id_int)
        ]

    def create_tag(self, name: str) -> Tag:
        normalized_name = self._normalized_tag_name(name)
        row = self._db.create_or_get_tag(normalized_name)
        if row is None:
            raise TagServiceError("Tag could not be created.")

        stored = self._db.get_tag(int(row[0]))
        if stored is None:
            raise TagServiceError("Tag could not be loaded.")
        return self._tag_from_row(stored)

    def rename_tag(self, tag_id: str, new_name: str) -> Tag:
        tag_id_int = self._tag_numeric_id(tag_id, "tag")
        normalized_name = self._normalized_tag_name(new_name)

        try:
            updated = self._db.rename_tag(tag_id_int, normalized_name)
        except sqlite3.IntegrityError as exc:
            raise TagServiceError(
                "A tag with that name already exists."
            ) from exc

        if not updated:
            raise TagServiceError("Tag not found.")

        row = self._db.get_tag(tag_id_int)
        if row is None:
            raise TagServiceError("Tag not found.")
        return self._tag_from_row(row)

    def delete_tag(self, tag_id: str) -> None:
        tag_id_int = self._tag_numeric_id(tag_id, "tag")
        if not self._db.delete_tag(tag_id_int):
            raise TagServiceError("Tag not found.")

    def add_tag_to_article(
        self,
        article_id: str,
        tag_id: str,
    ) -> None:
        article_id_int = self._tag_numeric_id(article_id, "article")
        tag_id_int = self._tag_numeric_id(tag_id, "tag")
        self._ensure_tag_targets(article_id, tag_id_int)
        self._db.add_article_tag(article_id_int, tag_id_int)

    def remove_tag_from_article(
        self,
        article_id: str,
        tag_id: str,
    ) -> None:
        article_id_int = self._tag_numeric_id(article_id, "article")
        tag_id_int = self._tag_numeric_id(tag_id, "tag")
        self._ensure_tag_targets(article_id, tag_id_int)
        self._db.remove_article_tag(article_id_int, tag_id_int)

    def list_articles_by_tags(
        self,
        tag_ids: list[str],
    ) -> list[Article]:
        if not tag_ids:
            return []

        numeric_ids = [
            self._tag_numeric_id(tag_id, "tag")
            for tag_id in dict.fromkeys(tag_ids)
        ]
        return [
            self._article_from_collection_row(row)
            for row in self._db.get_articles_by_tag_ids(numeric_ids)
        ]

    def fetch_article_content(self, article_id: str, force: bool = False) -> str:
        article = self.get_article(article_id)
        if article is None:
            return "Article not found."

        if not force and article.fetch_status == "success":
            return "Article content already fetched."

        detail = self._db.get_article_detail(int(article_id))
        if detail is None:
            return "Article detail not found."

        stored_title, _, stored_link = detail
        _, link = self._normalise_title_and_link(
            stored_title,
            stored_link,
        )
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

    def delete_feeds(self, feed_ids: Collection[str]) -> None:
        normalized_ids: list[int] = []
        for feed_id in feed_ids:
            try:
                numeric_id = int(feed_id)
            except (TypeError, ValueError) as exc:
                raise FeedDeletionError(
                    "Invalid feed identifier."
                ) from exc
            if numeric_id not in normalized_ids:
                normalized_ids.append(numeric_id)

        if not normalized_ids:
            raise FeedDeletionError("No feeds were selected.")

        if self._db.delete_feeds(normalized_ids):
            return

        raise FeedDeletionError(
            "One or more feeds were not found, so nothing was deleted."
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

    def translate_article_title(
        self,
        article_id: str,
        target_language: str = "zh",
        force: bool = False,
    ) -> str:
        article = self.get_article(article_id)
        if article is None:
            return "Article not found."

        if not force and article.translated_title:
            return "Article title already translated."

        if self._translator is None:
            return "Translation service is not configured."

        if not article.title:
            return "Article has no title to translate."

        result = self._translator.translate(article.title, target_language)

        if result.success:
            self._db.save_article_translated_title(
                int(article_id),
                result.translated_text,
                status="success",
                error=None,
            )
            return f"Article title translated to {target_language} successfully."
        else:
            self._db.save_article_translated_title(
                int(article_id),
                "",
                status="failed",
                error=result.error_message,
            )
            return f"Failed to translate article title: {result.error_message}"

    def _list_articles_for_feed(
        self,
        feed_id: str,
        source_title: str | None = None,
    ) -> list[Article]:
        feed_id_int = int(feed_id)

        if source_title is None:
            source_title = self._feed_title(feed_id)

        articles: list[Article] = []
        for (
            article_id,
            stored_title,
            published,
            is_starred,
            translated_title,
        ) in self._db.get_articles_by_feed(feed_id_int):
            detail = self._db.get_article_detail(article_id)
            stored_link = detail[2] if detail is not None else ""
            title, _link = self._normalise_title_and_link(stored_title, stored_link)
            display_title = translated_title or title
            meta = escape(published or "")
            articles.append(
                Article(
                    id=str(article_id),
                    feed_id=str(feed_id),
                    title=display_title,
                    source_title=source_title or "",
                    content_html=f"<p>{meta}</p>" if meta else "",
                    is_starred=bool(is_starred),
                    translated_title=translated_title or "",
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

    def _article_from_collection_row(self, row) -> Article:
        (
            article_id,
            feed_id,
            stored_title,
            stored_link,
            published,
            is_starred,
            source_title,
        ) = row
        title, _link = self._normalise_title_and_link(
            stored_title,
            stored_link,
        )
        meta = escape(published or "")
        return Article(
            id=str(article_id),
            feed_id=str(feed_id),
            title=title,
            source_title=source_title or "",
            content_html=f"<p>{meta}</p>" if meta else "",
            is_starred=bool(is_starred),
        )

    @staticmethod
    def _tag_numeric_id(value: str, label: str) -> int:
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise TagServiceError(
                f"Invalid {label} identifier."
            ) from exc

    @staticmethod
    def _normalized_tag_name(name: str) -> str:
        normalized = " ".join(str(name).split())
        if not normalized:
            raise TagServiceError("Tag name cannot be empty.")
        if len(normalized) > 64:
            raise TagServiceError("Tag name is too long.")
        return normalized

    @staticmethod
    def _tag_from_row(row) -> Tag:
        return Tag(
            id=str(row[0]),
            name=str(row[1]),
            article_count=int(row[2]),
        )

    def _ensure_tag_targets(
        self,
        article_id: str,
        tag_id: int,
    ) -> None:
        if self.get_article(article_id) is None:
            raise TagServiceError("Article not found.")
        if self._db.get_tag(tag_id) is None:
            raise TagServiceError("Tag not found.")

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
