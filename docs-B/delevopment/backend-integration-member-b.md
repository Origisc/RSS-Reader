# Member B Backend Integration

## Goal

Connect Member B's PySide6 UI service boundary to Member A's backend while
keeping the UI independently testable:

- add, import, refresh, and delete feeds;
- list and read locally cached articles;
- fetch full article HTML;
- clean Reader content and convert it to Markdown;
- translate article content through the shared Provider abstraction.

## Integration Decisions

`src/mercury/services/backend_article_service.py` remains the adapter between
the UI and the backend.

- The UI depends only on the `ArticleService` protocol.
- Feed operations use `FeedUseCase`, `DBManager`, and the OPML importer.
- Article processing uses the backend fetcher, cleaner, and Markdown converter.
- Translation receives `TranslationService` by constructor injection. The
  adapter does not choose a vendor, model, Base URL, API Key, or mock fallback.
- `ReaderDocument.from_article()` exposes persisted raw, cleaned HTML, and
  Markdown content while preserving the feed summary as a fallback.
- `MockArticleService` remains available for isolated UI development.

## Automated Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

The tests use in-memory databases, local HTML fixtures, and deterministic mock
Providers. They do not use the network, real credentials, or real LLM calls.

## Manual Verification

1. Run `.\.venv\Scripts\python.exe src\mercury\main.py`.
2. Add or import a feed and refresh it.
3. Select an entry and switch between Original, Cleaned HTML, and Markdown.
4. Confirm missing or failed processing results still show the original.
5. Delete a feed and confirm its cached entries disappear.
6. Restart the application and confirm remaining local data is still readable.

## Deferred Work

- Network-backed operations should move to a worker so slow requests never
  block the UI thread.
- The comparison UI will consume original and translated paragraph pairs in a
  later task.
