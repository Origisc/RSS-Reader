# LLM Provider Interface Decision

## Status

Accepted and completed for Stage 3. The HTTP adapter and local SQLite
configuration storage are connected in the production composition.

## Decision

- Every AI workflow accepts the same `LLMProvider` protocol.
- Provider calls receive an `LLMRequest` and return an `LLMResponse`.
  `LLMRequest.temperature` is optional; deterministic workflows such as
  translation may set it to `0`, while other workflows can omit it.
- Provider configuration contains only user-supplied Base URL, model name, optional API Key, and timeout.
- Business logic must not contain a vendor name, fixed production model, Base URL, or API Key.
- API Keys are excluded from configuration representations and must not enter logs or user-facing errors.
- Automated tests use `MockLLMProvider` and never access a real network or credential.

## HTTP Adapter

- `HTTPChatCompletionsProvider` implements the shared `LLMProvider` protocol.
- The user-supplied Base URL is treated as an API root. The adapter appends
  `/chat/completions` unless the configured URL already ends with that path.
- Requests contain the configured model and standard system/user message
  objects. An `Authorization: Bearer` header is added only when the user
  supplies an API Key.
- Each Agent owns an `HTTPChatCompletionsProvider` backed by its own
  `ProviderConfigStore` profile. Settings saved while the application is
  running therefore apply to that Agent's next request without rebuilding the
  window.
- Connection testing accepts the dialog's unsaved configuration and sends only
  a short explicit acknowledgement prompt, never article content.

## Configuration Storage Boundary

`ProviderConfigStore` remains the only configuration boundary used by the UI
and Provider. `InMemoryProviderConfigStore` is retained for deterministic
tests. Production injects three profiled `SQLiteProviderConfigStore`
instances for Summary, Translation, and Tag. They store independent
user-selected configurations in the existing local `database.db`. A one-time
migration copies the former shared configuration to all three profiles, after
which they can be edited or disabled independently. The file is excluded from
Git and is never synchronized by Mercury.

Every database operation uses a short-lived connection. This allows Summary
and Translation jobs to run in worker threads without sharing a SQLite
connection created by the UI thread.

## AI Result Persistence

- `SQLiteSummaryResultStore` saves structured summaries and loads the latest
  result for an article after restart.
- `SQLiteTranslationResultStore` saves the translation header and all
  paragraph rows in one transaction, preserving paragraph order and failure
  fallback metadata.
- Result history is capped per article to avoid unbounded local growth.
- Storage failures remain non-fatal: generated content stays available in the
  current UI and the base article remains readable.

## Failure Contract

Provider failures use `LLMProviderError` with a user-readable message. Summary and Translation workflows must catch this error and preserve the base article reading experience.

## Completed Follow-up

Task 3.1.2 added the Provider-neutral settings UI and injectable
connection-test interaction. The later Agents settings page gives
`SummaryAgent`, `TranslationAgent`, and `TagAgent` independent Provider
profiles while preserving the same `LLMProvider` protocol. Automated tests
replace HTTP transport and never access a real network. Production injects the
profiled SQLite Provider stores plus Summary and Translation result stores;
restart and migration round trips are covered by
`tests/test_ai_persistence.py`.
