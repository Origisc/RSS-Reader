# Read State Interface Decision

## Status

Accepted for the Member B UI prototype; Member A persistence adapter pending.

## Decision

- An article becomes read only after its detail is successfully loaded and displayed.
- The reader exposes an explicit action to mark the current article unread again.
- Read and unread colors are theme-aware: unread uses the primary high-contrast text color, while read uses a secondary gray.
- Every Feed row displays the number of unread articles belonging to that Feed.
- UI code depends on a `ReadStateStore` protocol and never writes the database directly.

## UI Contract

```python
class ReadStateStore(Protocol):
    def is_read(self, article_id: str) -> bool: ...
    def set_read(self, article_id: str, is_read: bool) -> None: ...
```

Member B provides an in-memory implementation for independent UI development and testing.

## Member A Integration Target

Member A can later implement a local adapter backed by the planned `reading_states` storage module. The adapter should use the stable article ID, persist `is_read`, and optionally record `read_at`. Replacing the in-memory store must not require UI changes.

## Rejected Alternatives

- A dwell timer was rejected because it adds timing and focus edge cases.
- Scroll-depth detection was rejected because short articles and partially loaded content make it unreliable.
- Manual-only marking was rejected because it creates unnecessary interaction overhead.
