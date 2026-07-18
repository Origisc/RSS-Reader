# Summary Result Interface Decision

## Status

Accepted for Task 3.2.1 Member B development; persistent repository pending.

## Decision

- `SummaryAgent` accepts a single `LLMProvider` abstraction and never selects a vendor, model, Base URL, or credential.
- `SummarySource` chooses content in this order: Cleaned Markdown, Cleaned HTML, raw HTML.
- `SummaryOptions` carries the requested language, detail level, and optional custom system prompt.
- `SummaryResult` always returns a structured status and error code so the later UI can translate failures without losing the article body.
- Successful results are written through `SummaryResultStore`; no Agent code imports SQLite or a concrete repository.
- A storage failure returns `GENERATED_NOT_SAVED` while preserving the generated summary text for the current session.

## Privacy and Failure Handling

Calling `summarize()` is the explicit user-triggered boundary at which selected article content may be sent to the configured Provider. Provider errors do not escape into the reader workflow. A configured API Key is removed if a Provider error accidentally contains it.

## Storage Integration Boundary

Member B provides the repository protocol and deterministic in-memory implementation. Member A can implement the same `save()` and `latest_for_article()` methods using the local settings/database layer without changing `SummaryAgent` or its UI consumer.

## Deferred Work

- Task 3.2.2 owns the asynchronous Summary UI, regeneration action, timestamps, and localized error presentation.
- Cross-process persistence remains with the local storage adapter owned by Member A.
