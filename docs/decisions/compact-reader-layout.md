# Compact Reader Layout Decision

## Status

Accepted for the Member B desktop UI.

## Decision

- The primary surface remains a resizable three-column layout: Feeds/Tags, Entries, and Reader.
- Feeds and tag browsing share the left column through an exclusive tab switch. Tag browsing does not allocate another permanent column.
- Article-tag editing is a bounded overlay inside the Reader surface. It can be closed and restored from the Reader control strip or View menu, and never becomes a window-wide dock.
- Feed actions stay beside the Feeds heading or in its small dropdown. Preferences, AI settings, and help remain in menus, so the duplicated main toolbar is removed.
- Entries expose an in-memory unread filter in the column header. It uses the existing local read-state data and does not add storage or network dependencies.
- Reader representation, tag visibility, Summary visibility, and read state remain in one compact Reader control strip. Normal representation status text is hidden; fallback or cleaning errors remain visible.
- Summary starts collapsed as a narrow strip below Reader and expands in place.
- Starred is intentionally not implemented or simulated until its domain and storage contract are designed.

## Constraints

The layout remains pure PySide6 and uses injected services already available to the window. The tag surfaces remain presentational until a local tag service exists; they do not call an LLM or persist fabricated state.
