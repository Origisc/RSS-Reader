from typing import Protocol

from mercury.models.article import Article, Feed


class ArticleService(Protocol):
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