# Member B Read State UI

## Goal

Implement the selected read-state behavior without changing Member A's database:

- Opening a successfully loaded article marks it read.
- The current article can be marked unread again from the Reader toolbar.
- Unread Entries use bold, high-contrast text.
- Read Entries use secondary gray text.
- Feed rows show their real unread article count.

## Theme Behavior

- Light theme: unread `#1f2933`, read `#8a949e`.
- Dark/system theme: unread `#e5edf5`, read `#778391`.
- Selected rows continue using the theme selection color.

## Boundary

`InMemoryReadStateStore` provides independent UI verification and performs no file, database, network, or LLM access. The integration decision is recorded in `docs/decisions/read-state-interface.md`.

Member A can later inject a persistent adapter backed by the planned local `reading_states` storage. The UI does not require modification when that adapter is ready.

## Offline Verification

```powershell
uv run python -m unittest tests.test_read_state tests.test_i18n -v
```

## Manual Verification

1. Run `uv run python src/mercury/main.py`.
2. Confirm unread Entries are bold and high contrast.
3. Open an article and confirm it becomes gray.
4. Confirm its Feed unread count decreases by one.
5. Click “标记为未读” in the Reader toolbar.
6. Confirm the Entry returns to bold and the Feed count increases.
7. Switch light/dark themes and confirm both states remain readable.

## Current Limitation

Read state lasts for the current process only. Restart persistence is pending Member A's local storage adapter.
