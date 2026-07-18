# Member B LLM Provider Foundation

## Goal

Implement `plan.md` Task 3.1.1 as an offline, provider-neutral foundation:

- Unified Provider protocol.
- Base URL, model, optional API Key, and timeout configuration.
- Safe configuration validation.
- API Key redaction from `repr` and errors.
- Deterministic Mock Provider.
- Replaceable configuration Store protocol.

## Boundary

This task performs no network request and does not include a real vendor adapter. `InMemoryProviderConfigStore` enables independent development; persistent local storage waits for Member A's repository adapter.

No Provider call is connected to article reading. Basic RSS reading therefore remains fully usable without any AI configuration.

## Offline Verification

```powershell
uv run python -m unittest tests.test_llm_provider -v
```

The tests cover deterministic responses, request recording, connection success/failure, configuration validation, in-memory save/load, empty prompts, user-readable errors, and API Key redaction.

## Next Task

Task 3.1.2 can build an AI settings page against these interfaces, using `MockLLMProvider` for connection testing and never displaying the complete API Key.
