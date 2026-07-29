from enum import StrEnum


class FeedImportErrorCode(StrEnum):
    EMPTY_SOURCE = "empty_source"
    FILE_NOT_FOUND = "file_not_found"
    NOT_A_FILE = "not_a_file"
    FILE_READ_FAILED = "file_read_failed"
    UNSUPPORTED_SCHEME = "unsupported_scheme"
    NETWORK_FAILED = "network_failed"
    INVALID_FEED = "invalid_feed"
    INVALID_OPML = "invalid_opml"
    OPML_NO_FEEDS = "opml_no_feeds"
    STORAGE_FAILED = "storage_failed"


_FALLBACK_MESSAGES = {
    FeedImportErrorCode.EMPTY_SOURCE: (
        "No Feed URL or local file path was provided."
    ),
    FeedImportErrorCode.FILE_NOT_FOUND: "Local file was not found.",
    FeedImportErrorCode.NOT_A_FILE: "The selected path is not a file.",
    FeedImportErrorCode.FILE_READ_FAILED: (
        "The local file could not be read as UTF-8."
    ),
    FeedImportErrorCode.UNSUPPORTED_SCHEME: (
        "The Feed source scheme is unsupported."
    ),
    FeedImportErrorCode.NETWORK_FAILED: "The Feed could not be downloaded.",
    FeedImportErrorCode.INVALID_FEED: (
        "The source is not a valid RSS or Atom Feed."
    ),
    FeedImportErrorCode.INVALID_OPML: (
        "The selected file is not a valid OPML document."
    ),
    FeedImportErrorCode.OPML_NO_FEEDS: (
        "The OPML document does not contain any importable feeds."
    ),
    FeedImportErrorCode.STORAGE_FAILED: (
        "The imported Feed could not be saved locally."
    ),
}


class FeedImportError(RuntimeError):
    """Structured import failure suitable for UI localization."""

    def __init__(
        self,
        code: FeedImportErrorCode,
        *,
        source: str = "",
        detail: str = "",
    ) -> None:
        self.code = code
        self.source = source
        self.detail = detail
        message = _FALLBACK_MESSAGES[code]
        if source:
            message = f"{message} Source: {source}"
        if detail:
            message = f"{message} Details: {detail}"
        super().__init__(message)
