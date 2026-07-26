from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SummaryDetail(StrEnum):
    BRIEF = "brief"
    STANDARD = "standard"
    DETAILED = "detailed"


class SummarySourceFormat(StrEnum):
    CLEANED_MARKDOWN = "cleaned_markdown"
    CLEANED_HTML = "cleaned_html"
    RAW_HTML = "raw_html"


class SummaryStatus(StrEnum):
    GENERATED = "generated"
    GENERATED_NOT_SAVED = "generated_not_saved"
    FAILED = "failed"


class SummaryErrorCode(StrEnum):
    INVALID_INPUT = "invalid_input"
    PROVIDER_NOT_CONFIGURED = "provider_not_configured"
    PROVIDER_FAILURE = "provider_failure"
    EMPTY_RESPONSE = "empty_response"
    WRONG_LANGUAGE = "wrong_language"
    STORAGE_FAILURE = "storage_failure"


@dataclass(frozen=True, slots=True)
class SummaryResult:
    """Structured result suitable for persistence and later UI translation."""

    article_id: str
    text: str
    language: str
    detail_level: SummaryDetail
    source_format: SummarySourceFormat
    generated_at: datetime
    provider_model: str
    status: SummaryStatus = SummaryStatus.GENERATED
    error_code: SummaryErrorCode | None = None
    error_message: str = ""

    @property
    def has_summary(self) -> bool:
        return bool(self.text.strip())

    @property
    def is_saved(self) -> bool:
        return self.status is SummaryStatus.GENERATED

    @property
    def succeeded(self) -> bool:
        return self.status is not SummaryStatus.FAILED and self.has_summary
