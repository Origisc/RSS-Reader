from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TranslationSourceFormat(StrEnum):
    CLEANED_MARKDOWN = "cleaned_markdown"
    CLEANED_HTML = "cleaned_html"
    RAW_HTML = "raw_html"


class TranslationParagraphStatus(StrEnum):
    TRANSLATED = "translated"
    PARTIAL = "partial"
    FAILED = "failed"


class TranslationStatus(StrEnum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class TranslationErrorCode(StrEnum):
    INVALID_INPUT = "invalid_input"
    PROVIDER_NOT_CONFIGURED = "provider_not_configured"
    PROVIDER_FAILURE = "provider_failure"
    EMPTY_RESPONSE = "empty_response"
    WRONG_LANGUAGE = "wrong_language"
    INCOMPLETE_RESPONSE = "incomplete_response"
    STORAGE_FAILURE = "storage_failure"


@dataclass(frozen=True, slots=True)
class TranslationParagraph:
    index: int
    original_text: str
    translated_text: str
    status: TranslationParagraphStatus
    segment_count: int
    translated_segment_count: int
    error_code: TranslationErrorCode | None = None
    error_message: str = ""

    @property
    def has_translation(self) -> bool:
        return bool(self.translated_text.strip())


@dataclass(frozen=True, slots=True)
class TranslationResult:
    """Paragraph-aligned translation result that always retains originals."""

    article_id: str
    target_language: str
    paragraphs: tuple[TranslationParagraph, ...]
    source_format: TranslationSourceFormat
    generated_at: datetime
    provider_model: str
    status: TranslationStatus
    is_saved: bool = False
    error_code: TranslationErrorCode | None = None
    error_message: str = ""
    storage_error_code: TranslationErrorCode | None = None
    storage_error_message: str = ""

    @property
    def has_translations(self) -> bool:
        return any(paragraph.has_translation for paragraph in self.paragraphs)

    @property
    def original_paragraphs(self) -> tuple[str, ...]:
        return tuple(
            paragraph.original_text
            for paragraph in self.paragraphs
        )

    @property
    def succeeded(self) -> bool:
        return self.status is TranslationStatus.COMPLETED
