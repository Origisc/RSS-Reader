# Feed deletion — member B verification

## Scope

Member B provides extended Feed selection, destructive confirmation,
translated messages, UI refresh, backend adapter, and production entry-point
injection. Persistent single and batch deletion are exposed through
`FeedDeletionService`.

## Automated verification

```powershell
uv run python -m unittest tests.test_feed_deletion tests.test_backend_article_service tests.test_main_entry tests.test_sidebar tests.test_i18n -v
```

The tests do not access the network or the user's database.

## Manual verification

1. Start Mercury normally; the production entry point injects the backend adapter.
2. Click **Select multiple / 多选删除** to enter batch-delete mode.
3. Click any real Feeds, including non-contiguous rows, without holding Ctrl
   or Shift. Each click toggles that Feed, and the action displays the current
   selected count. Use **Cancel / 取消** to leave the mode without deleting.
4. Click **Delete selected / 删除所选**. The warning must show the exact count
   and list every selected Feed. All Feeds and Starred are excluded
   automatically.
5. Cancel the warning and confirm that every selected Feed remains.
6. Repeat and confirm deletion. Confirm that all selected Feeds and their
   entries disappear together and the reader returns to the welcome view.
7. Include a stale or missing ID in the service test and confirm that no Feed
   in the batch is deleted.
8. Switch between Chinese and English and repeat the dialog check.
9. In the isolated UI test, start without a deletion adapter and confirm that
   the UI reports a missing service instead of reporting deletion success.

## Integrated adapter

Inject an implementation of:

```python
def delete_feed(feed_id: str) -> None: ...
def delete_feeds(feed_ids: Collection[str]) -> None: ...
```

`BackendArticleService.delete_feeds()` validates and converts the complete ID
set before calling `DBManager.delete_feeds()`. The database checks that every
Feed still exists, then removes all selected rows in one SQLite transaction.
Any validation or write failure leaves the entire batch intact.
