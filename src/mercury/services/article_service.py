from typing import Protocol

from mercury.models.article import Article, Feed
from mercury.services.tag_service import TagService


class StarredEntryError(RuntimeError):
    """A local starred-state write failure suitable for UI fallback."""


class StarredEntryService(Protocol):
    """Local-first starred entry boundary used by the UI."""

    def set_starred(self, article_id: str, is_starred: bool) -> None:
        """Persist an article's starred state."""
        ...

    def list_starred_articles(self) -> list[Article]:
        """Return starred articles across every feed."""
        ...

    def count_starred_articles(self) -> int:
        """Return the global number of starred articles."""
        ...


class ArticleService(StarredEntryService, TagService, Protocol):
    """UI 获取订阅源和文章时使用的统一接口。"""

    def list_feeds(self) -> list[Feed]:
        """返回全部订阅源。"""
        ...

    def list_articles(self, feed_id: str | None = None) -> list[Article]:
        """返回文章；提供 feed_id 时只返回对应订阅源的文章。"""
        ...

    def get_article(self, article_id: str) -> Article | None:
        """按照文章 ID 获取文章详情。"""
        ...

    def fetch_article_content(
        self,
        article_id: str,
        force: bool = False,
    ) -> str:
        """抓取文章正文内容，并返回结果说明。"""
        ...

    def clean_article_content(
        self,
        article_id: str,
        force: bool = False,
    ) -> str:
        """清洗文章内容，并返回结果说明。"""
        ...

    def convert_to_markdown(
        self,
        article_id: str,
        force: bool = False,
    ) -> str:
        """将文章内容转换为 Markdown，并返回结果说明。"""
        ...

    def translate_article_content(
        self,
        article_id: str,
        target_language: str = "zh",
        force: bool = False,
    ) -> str:
        """翻译文章内容，并返回结果说明。"""
        ...

    def add_feed(self, xml_url: str) -> str:
        """添加单个 Feed，并返回用户可理解的结果说明。"""
        ...

    def import_opml(self, file_path: str) -> str:
        """导入 OPML，并返回用户可理解的结果说明。"""
        ...

    def refresh_all(self) -> str:
        """刷新全部订阅源，并返回用户可理解的结果说明。"""
        ...
