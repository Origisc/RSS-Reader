# Feed deletion interface

## Context

The sidebar needs a safe way to delete a subscription. The UI is owned by
member B, while persistent feed and article storage is owned by member A.
Mercury's UI must not execute SQL or directly modify local storage.

## Decision

The UI depends on this narrow interface:

```python
class FeedDeletionService(Protocol):
    def delete_feed(self, feed_id: str) -> None: ...
```

- Deletion is allowed only after an explicit destructive confirmation dialog.
- The confirmation names the selected feed and states that its locally cached
  articles will also be removed and that the action cannot be undone.
- The cancel path is safe and performs no service call.
- Member A's adapter must delete the subscription and its cached articles in
  one local transaction. It must either complete fully or leave both intact.
- After success, the UI reloads feeds and entries through `ArticleService`.
- If no deletion adapter is injected, the UI displays a clear integration
  message and does not report success.

## Consequences

Member B can independently verify the complete interaction with an in-memory
fake. Persistent deletion remains an explicit member A integration task and
does not leak database responsibilities into `ui/`.
