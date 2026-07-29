from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from domain.feed.import_errors import (
    FeedImportError,
    FeedImportErrorCode,
)


@dataclass(frozen=True, slots=True)
class ResolvedFeedSource:
    value: str
    local_path: Path | None

    @property
    def is_local(self) -> bool:
        return self.local_path is not None


def resolve_local_file(
    file_path: str,
    *,
    base_directory: Path | None = None,
) -> Path:
    raw_path = str(file_path).strip()
    if not raw_path:
        raise FeedImportError(FeedImportErrorCode.EMPTY_SOURCE)

    parsed = urlparse(raw_path)
    if parsed.scheme and not _looks_like_windows_drive(raw_path):
        raise FeedImportError(
            FeedImportErrorCode.UNSUPPORTED_SCHEME,
            source=raw_path,
        )

    try:
        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            candidate = (base_directory or Path.cwd()) / candidate
        candidate = candidate.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise FeedImportError(
            FeedImportErrorCode.FILE_NOT_FOUND,
            source=raw_path,
            detail=str(exc),
        ) from exc

    if not candidate.exists():
        raise FeedImportError(
            FeedImportErrorCode.FILE_NOT_FOUND,
            source=str(candidate),
        )
    if not candidate.is_file():
        raise FeedImportError(
            FeedImportErrorCode.NOT_A_FILE,
            source=str(candidate),
        )

    return candidate


def resolve_feed_source(
    source: str,
    *,
    base_directory: Path | None = None,
) -> ResolvedFeedSource:
    normalized = str(source).strip()
    if not normalized:
        raise FeedImportError(FeedImportErrorCode.EMPTY_SOURCE)

    parsed = urlparse(normalized)
    if parsed.scheme.casefold() in {"http", "https"}:
        return ResolvedFeedSource(normalized, None)

    if parsed.scheme and not _looks_like_windows_drive(normalized):
        raise FeedImportError(
            FeedImportErrorCode.UNSUPPORTED_SCHEME,
            source=normalized,
        )

    path = resolve_local_file(
        normalized,
        base_directory=base_directory,
    )
    return ResolvedFeedSource(str(path), path)


def read_utf8_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise FeedImportError(
            FeedImportErrorCode.FILE_READ_FAILED,
            source=str(path),
            detail=str(exc),
        ) from exc


def _looks_like_windows_drive(value: str) -> bool:
    return (
        len(value) >= 3
        and value[0].isalpha()
        and value[1] == ":"
        and value[2] in {"\\", "/"}
    )
