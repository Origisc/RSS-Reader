# Release readiness verification

## Goal

Verify that a GitHub source download can be installed, tested, and started without relying on an existing virtual environment, repository database, API key, or online LLM.

## Source installation

Run from a clean checkout:

```bash
uv python install 3.13
uv sync --locked
uv run python -c "import mercury, core, domain"
uv run pytest -q
uv run mercury
```

Expected results:

- `uv sync --locked` installs the locked dependencies and the `rss-reader` project itself.
- The package imports succeed even when Python is launched outside the repository directory.
- Tests run with Qt in offscreen mode and do not require an API key or unstable network.
- `uv run mercury` starts the application and creates `database.db` in the per-user application data directory.

## Basic reading gate

The automated suite covers the following offline paths:

- RSS/Atom and OPML parsing, including relative and absolute local paths.
- Feed/article persistence, refresh deduplication, read state, safe deletion, stars, and tags.
- Original, Cleaned HTML, and Markdown Reader representations and failure fallback.
- English/Simplified Chinese runtime UI text.
- No-Provider startup and AI failure isolation from basic reading.

## OpenAI-compatible Provider gate

The Provider adapter is verified with local transports for both of these URL shapes:

- OpenAI: `https://api.openai.com/v1/chat/completions`
- Gemini OpenAI compatibility: `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`

The tests assert Bearer authentication, selected model forwarding, Chat Completions messages, compatible response parsing, secret redaction, and readable errors for invalid request/model, authentication, billing, permission, missing path/model, rate limit, server error, timeout, proxy, TLS, network, invalid JSON, and incompatible responses.

Real cloud requests are intentionally not part of automated verification. They require a user-owned API key, an API-enabled account, a currently available model ID, and an explicit click on **Test Connection**.

## Packaged application gate

Use the same Windows command as the GitHub release workflow:

```bash
uv run --no-sync python -m PyInstaller --noconfirm --clean --onefile --windowed --name Mercury-Windows-x64 --paths src --paths . main.py
```

Confirm that `dist/Mercury-Windows-x64.exe` starts and initializes an isolated local database. GitHub Actions performs the corresponding build and offline tests on Windows, macOS, and Linux.

## Local-data safety

- `.env`, `password/`, virtual environments, build output, and `database.db` are ignored by Git.
- Before publishing, scan tracked files for credential prefixes and confirm no database or credential file is tracked.
- API keys are user configuration. Never include a real key in fixtures, screenshots, logs, commits, or release artifacts.
