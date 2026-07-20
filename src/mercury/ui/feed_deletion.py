from typing import Protocol


class FeedDeletionService(Protocol):
    """Boundary used by the UI to request persistent feed deletion."""

    def delete_feed(self, feed_id: str) -> None:
        """Delete one feed and its locally cached articles."""
        ...
