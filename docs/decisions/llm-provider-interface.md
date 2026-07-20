# LLM Provider Interface Decision

## Status

Accepted for Stage 3 Member B development; persistent storage adapter pending.

## Decision

- Every AI workflow accepts the same `LLMProvider` protocol.
- Provider calls receive an `LLMRequest` and return an `LLMResponse`.
- Provider configuration contains only user-supplied Base URL, model name, optional API Key, and timeout.
- Business logic must not contain a vendor name, fixed production model, Base URL, or API Key.
- API Keys are excluded from configuration representations and must not enter logs or user-facing errors.
- Automated tests use `MockLLMProvider` and never access a real network or credential.

## Configuration Storage Boundary

Member B provides `ProviderConfigStore` and an in-memory implementation for independent UI and Agent development. Member A can later inject a local settings repository without changing Provider consumers.

## Failure Contract

Provider failures use `LLMProviderError` with a user-readable message. Summary and Translation workflows must catch this error and preserve the base article reading experience.

## Deferred Work

- Real standard-API adapters are user-configured integrations and must not be required by automated tests.
- Local persistence belongs to the storage integration point owned by Member A.

## Completed Follow-up

Task 3.1.2 added the Provider-neutral settings UI and injectable connection-test interaction. Without a real adapter, the application explicitly reports that no network request was made.
