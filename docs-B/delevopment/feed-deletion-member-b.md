# Feed deletion — member B verification

## Scope

Member B provides the sidebar action, destructive confirmation, translated
messages, UI refresh, backend adapter, and production entry-point injection.
Persistent deletion is implemented by Member A and exposed through
`FeedDeletionService`.

## Automated verification

```powershell
uv run python -m unittest tests.test_feed_deletion tests.test_backend_article_service tests.test_main_entry tests.test_sidebar tests.test_i18n -v
```

The tests do not access the network or the user's database.

## Manual verification

1. Start Mercury normally; the production entry point injects the backend adapter.
2. Select a feed and open the feed actions dropdown.
3. Choose **Delete selected Feed**.
4. Cancel the warning and confirm that the feed remains.
5. Repeat and confirm deletion. Confirm that the feed and its entries disappear
   and the reader returns to the welcome view.
6. Switch between Chinese and English and repeat the dialog check.
7. In the isolated UI test, start without a deletion adapter and confirm that
   the UI reports a missing service instead of reporting deletion success.

## Integrated adapter

Inject an implementation of:

```python
def delete_feed(feed_id: str) -> None: ...
```

`BackendArticleService.delete_feed()` converts the UI string ID to the backend
integer ID, calls `FeedUseCase.remove_feed_by_id()`, and raises a service error
on failure so the UI can show the translated failure path.
