# Feed deletion — member B verification

## Scope

Member B provides the sidebar action, destructive confirmation, translated
messages, UI refresh, and a Mock-backed test. Persistent storage deletion is
implemented later by member A through `FeedDeletionService`.

## Automated verification

```powershell
uv run python -m unittest tests.test_feed_deletion tests.test_sidebar tests.test_i18n -v
```

The tests do not access the network or the user's database.

## Manual verification

1. Start Mercury with a `FeedDeletionService` adapter or the test fake.
2. Select a feed and open the feed actions dropdown.
3. Choose **Delete selected Feed**.
4. Cancel the warning and confirm that the feed remains.
5. Repeat and confirm deletion. Confirm that the feed and its entries disappear
   and the reader returns to the welcome view.
6. Switch between Chinese and English and repeat the dialog check.
7. Start without a deletion adapter and confirm that the UI explains the
   missing member A integration instead of reporting deletion success.

## Member A integration requirement

Inject an implementation of:

```python
def delete_feed(feed_id: str) -> None: ...
```

The implementation must remove the feed and its cached articles atomically and
raise an exception on failure so the UI can show the translated failure path.
