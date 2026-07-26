from typing import Protocol

from mercury.models.article import Article
from mercury.models.tag import Tag


class TagServiceError(RuntimeError):
    """A user-facing tag operation failed without affecting reading."""


class TagService(Protocol):
    """Local manual-tag boundary; it has no AI dependency."""

    def list_tags(self) -> list[Tag]:
        ...

    def list_article_tags(self, article_id: str) -> list[Tag]:
        ...

    def create_tag(self, name: str) -> Tag:
        ...

    def rename_tag(self, tag_id: str, new_name: str) -> Tag:
        ...

    def delete_tag(self, tag_id: str) -> None:
        ...

    def add_tag_to_article(
        self,
        article_id: str,
        tag_id: str,
    ) -> None:
        ...

    def remove_tag_from_article(
        self,
        article_id: str,
        tag_id: str,
    ) -> None:
        ...

    def list_articles_by_tags(
        self,
        tag_ids: list[str],
    ) -> list[Article]:
        """Return articles matching every selected tag."""
        ...
