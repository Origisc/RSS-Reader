# Member B LLM Provider Foundation

## Goal

Implement `plan.md` Task 3.1.1 as an offline, provider-neutral foundation:

- Unified Provider protocol.
- Base URL, model, optional API Key, and timeout configuration.
- Safe configuration validation.
- API Key redaction from `repr` and errors.
- Deterministic Mock Provider.
- Replaceable configuration Store protocol.

## Original Boundary

Task 3.1.1 originally performed no network request and did not include a real
adapter. `InMemoryProviderConfigStore` enabled independent development;
persistent local storage still waits for Member A's repository adapter.

## Connected HTTP Follow-up

`HTTPChatCompletionsProvider` now implements the production protocol using only
the user-supplied Base URL, model, optional API Key, and timeout. `main.py`
shares it between connection testing, `SummaryAgent`, and `TranslationAgent`.
It reads the current configuration before each explicit AI request, while
basic RSS reading remains usable without configuration.

Automated tests inject an in-memory HTTP transport or patch `requests.post`;
they never access a real network or credential.

## Offline Verification

```powershell
uv run python -m unittest tests.test_llm_provider tests.test_http_llm_provider tests.test_ai_provider_integration -v
```

The tests cover deterministic responses, request construction, dynamic
configuration, connection success/failure, configuration validation,
in-memory save/load, timeout handling, malformed responses, and API Key
redaction.
