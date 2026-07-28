# Feed deletion interface

## Context

The sidebar needs a safe way to delete one or more subscriptions. The UI is
owned by member B, while persistent feed and article storage is owned by
member A. Mercury's UI must not execute SQL or directly modify local storage.

## Decision

The UI depends on this narrow interface:

```python
class FeedDeletionService(Protocol):
    def delete_feed(self, feed_id: str) -> None: ...
    def delete_feeds(self, feed_ids: Collection[str]) -> None: ...
```

- Deletion is allowed only after an explicit destructive confirmation dialog.
- Normal sidebar navigation remains single-selection. A dedicated batch-delete
  button switches the list into multi-selection mode, where each click toggles
  any real Feed without requiring Ctrl or Shift. A separate cancel action
  restores normal navigation.
- Virtual rows such as All Feeds and Starred are never deletion targets.
- Single-item confirmation names the Feed. Batch confirmation lists every
  selected Feed, gives the count, and states that cached articles are removed.
- The cancel path is safe and performs no service call.
- The backend adapter must delete all selected subscriptions and their cached
  articles in one local transaction. It must either complete fully or leave
  every selected Feed intact.
- After success, the UI reloads feeds and entries through `ArticleService`.
- If no deletion adapter is injected, the UI displays a clear integration
  message and does not report success.

## Consequences

`DBManager.delete_feeds()` validates the complete ID set before issuing one
transactional `DELETE`. SQLite foreign-key cascades remove related articles,
article-tag relations, and other article-owned local rows. The production
entry point injects `BackendArticleService` into `MainWindow`; database
responsibilities remain outside `ui/`.
