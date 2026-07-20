from typing import Protocol


class ReadStateStore(Protocol):
    """UI-facing contract for local article read state."""

    def is_read(self, article_id: str) -> bool:
        ...

    def set_read(self, article_id: str, is_read: bool) -> None:
        ...


class InMemoryReadStateStore:
    """Offline UI store; Member A can replace it with a local adapter."""

    def __init__(self, read_article_ids: set[str] | None = None) -> None:
        self._read_article_ids = set(read_article_ids or set())

    def is_read(self, article_id: str) -> bool:
        return article_id in self._read_article_ids

    def set_read(self, article_id: str, is_read: bool) -> None:
        if is_read:
            self._read_article_ids.add(article_id)
            return

        self._read_article_ids.discard(article_id)
