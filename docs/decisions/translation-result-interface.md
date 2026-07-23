# Translation Result Interface Decision

## Status

Accepted for Task 3.3.1 Member B development; local article persistence is
integrated.

## Decision

- `TranslationAgent` accepts the common `LLMProvider` abstraction and never chooses a vendor, production model, Base URL, or credential.
- `TranslationSource` selects Cleaned Markdown, then Cleaned HTML, then raw HTML.
- Markdown is split on paragraph boundaries. HTML paragraphs are extracted with the Python standard library while script and style content is ignored.
- Paragraphs longer than the configured segment size are split at punctuation or whitespace boundaries. Provider results are merged in original segment order.
- Every `TranslationParagraph` retains `original_text` and records translated, partial, or failed status. One failed paragraph or segment never stops later paragraphs.
- `TranslationResult` preserves paragraph order and reports completed, partial, or failed overall status.
- Results with at least one translation are saved through `TranslationResultStore`. Storage failure retains the generated translation in memory and returns a separate storage error.

## Privacy and Failure Handling

Calling `translate()` is the explicit boundary at which article text may be sent to the configured Provider. Provider failures become structured paragraph errors, unexpected exceptions expose no backend details, and a configured API Key is redacted if an adapter error includes it.

## Storage Integration Boundary

Member B's `TranslationAgent` retains its repository protocol and deterministic
in-memory implementation. Member A's article-level translation storage is
available through `DBManager.save_article_translated()` and is called by
`BackendArticleService`.

`BackendArticleService` receives `TranslationService` through constructor
injection. It never creates a vendor adapter, selects a model, reads credentials,
or silently substitutes a mock Provider. This keeps both translation paths on
the shared `LLMProvider.complete(LLMRequest)` contract.

## Deferred Work

- Task 3.3.2 owns asynchronous execution and original/translated paragraph comparison UI.
- A later adapter may unify `TranslationResultStore` history with the persisted
  article-level translation fields.
