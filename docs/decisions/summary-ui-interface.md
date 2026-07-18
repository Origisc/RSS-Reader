# Summary UI Interface Decision

## Status

Accepted for Task 3.2.2 Member B development.

## Decision

- `SummaryPanel` receives a `SummaryGenerator` callable and optional `SummaryResultLoader`; it never constructs a concrete Provider or performs Provider protocol work itself.
- Generation runs in `QThreadPool`. The article reader stays interactive and its content is never replaced by summary state.
- Each request receives a monotonically increasing token. Results from an article that is no longer selected are ignored by the UI.
- Regeneration keeps the previous summary visible until a new successful result arrives. A failed regeneration displays a localized error without discarding the earlier result.
- The panel exposes language, detail level, and optional custom Prompt controls and sends article content only after the user clicks Generate or Regenerate.
- Generated timestamps are rendered in the user's local timezone. A `GENERATED_NOT_SAVED` result remains viewable with a local-storage warning.

## Integration Boundary

The production application currently has no concrete online Provider adapter, so the default panel reports that the summary service is unavailable. After an article is selected, the Generate button remains visible and clicking it opens AI settings instead of silently doing nothing. Tests inject `SummaryAgent.summarize` backed by `MockLLMProvider`. A future composition root can create the configured Provider and pass the same callable without modifying UI code.

The current `ArticleService` exposes raw HTML only. `SummaryPanel` already accepts Cleaned Markdown and Cleaned HTML through `SummarySource`; once the Reader/cleaning service provides those representations, the composition layer can pass them through while preserving the existing priority contract.

## Failure Contract

Known `SummaryErrorCode` values map to localized UI messages. Unexpected worker or loader exceptions are replaced with a generic localized message, so backend details and credentials do not enter the interface.

Summary controls also set explicit text, placeholder, base, and popup-list colors. This avoids native Windows/Linux/macOS widget palettes falling back to unreadable black text in dark mode.

Closing the Summary dock only hides it. A checkable **View → Summary Panel** action tracks dock visibility and restores the same panel instance, including its in-session results and controls.

The Reader toolbar exposes the same visibility state as a prominent checkable Summary button with `Ctrl+Shift+S`. Hiding the dock removes both its content and title bar, does not cancel an active background request, and does not discard in-session results.

The Summary dock close control uses a programmatically drawn, theme-aware high-contrast icon instead of the native platform icon. The dark theme uses a red background with a thick white cross, while the light theme uses a pale red background with a dark red cross. This keeps the control visible across Qt platform styles.
