# LLM Provider Interface Decision

## Status

Accepted for Stage 3 Member B development; HTTP adapter connected and
persistent configuration storage pending.

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
- The adapter reads `ProviderConfigStore` for every completion. Settings saved
  while the application is running therefore apply to the next Summary or
  Translation request without rebuilding the window.
- Connection testing accepts the dialog's unsaved configuration and sends only
  a short explicit acknowledgement prompt, never article content.

## Configuration Storage Boundary

Member B provides `ProviderConfigStore` and an in-memory implementation for independent UI and Agent development. Member A can later inject a local settings repository without changing Provider consumers.

## Failure Contract

Provider failures use `LLMProviderError` with a user-readable message. Summary and Translation workflows must catch this error and preserve the base article reading experience.

## Deferred Work

- Local configuration persistence belongs to the storage integration point
  owned by Member A.

## Completed Follow-up

Task 3.1.2 added the Provider-neutral settings UI and injectable
connection-test interaction. The production composition now shares one
`HTTPChatCompletionsProvider` between connection testing, `SummaryAgent`, and
`TranslationAgent`. Automated tests replace its HTTP transport and never
access a real network.
