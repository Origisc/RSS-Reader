from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from html.parser import HTMLParser
import re
from typing import Protocol

from mercury.domain import (
    TranslationErrorCode,
    TranslationParagraph,
    TranslationParagraphStatus,
    TranslationResult,
    TranslationSourceFormat,
    TranslationStatus,
)
from mercury.llm import LLMProvider, LLMProviderError, LLMRequest


MIN_SEGMENT_CHARS = 20
MAX_SEGMENT_CHARS = 12_000
DEFAULT_SEGMENT_CHARS = 2_000

DEFAULT_TRANSLATION_SYSTEM_PROMPT = (
    "Translate the supplied article text faithfully. Preserve meaning, "
    "tone, names, technical terms, and uncertainty. Return only the translation."
)


@dataclass(frozen=True, slots=True)
class TranslationOptions:
    target_language: str = "Simplified Chinese"
    custom_prompt: str = ""
    max_segment_chars: int = DEFAULT_SEGMENT_CHARS


@dataclass(frozen=True, slots=True)
class TranslationSource:
    article_id: str
    title: str
    raw_html: str
    cleaned_markdown: str | None = None
    cleaned_html: str | None = None

    def preferred_content(
        self,
    ) -> tuple[TranslationSourceFormat, str] | None:
        candidates = (
            (
                TranslationSourceFormat.CLEANED_MARKDOWN,
                self.cleaned_markdown,
            ),
            (TranslationSourceFormat.CLEANED_HTML, self.cleaned_html),
            (TranslationSourceFormat.RAW_HTML, self.raw_html),
        )

        for source_format, content in candidates:
            if content is not None and content.strip():
                return source_format, content.strip()

        return None


class TranslationResultStore(Protocol):
    """Persistence boundary for Member A's future local repository."""

    def save(self, result: TranslationResult) -> None:
        ...

    def latest_for_article(
        self,
        article_id: str,
    ) -> TranslationResult | None:
        ...


class InMemoryTranslationResultStore:
    """Process-local result store for deterministic Agent and UI tests."""

    def __init__(self) -> None:
        self._results: dict[str, list[TranslationResult]] = {}

    def save(self, result: TranslationResult) -> None:
        self._results.setdefault(result.article_id, []).append(result)

    def latest_for_article(
        self,
        article_id: str,
    ) -> TranslationResult | None:
        results = self._results.get(article_id, [])

        if not results:
            return None

        return results[-1]


class _HTMLParagraphParser(HTMLParser):
    _BLOCK_TAGS = {
        "address",
        "article",
        "aside",
        "blockquote",
        "dd",
        "div",
        "dl",
        "dt",
        "figcaption",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "nav",
        "p",
        "pre",
        "section",
        "tr",
    }
    _IGNORED_TAGS = {"script", "style"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paragraphs: list[str] = []
        self._parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        lowered = tag.lower()
        if lowered in self._IGNORED_TAGS:
            self._ignored_depth += 1
            return

        if self._ignored_depth:
            return

        if lowered in self._BLOCK_TAGS and self._parts:
            self._flush()
        elif lowered == "br":
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in self._IGNORED_TAGS:
            self._ignored_depth = max(0, self._ignored_depth - 1)
            return

        if self._ignored_depth:
            return

        if lowered in self._BLOCK_TAGS:
            self._flush()
        elif lowered in {"td", "th"}:
            self._parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self._parts.append(data)

    def close(self) -> None:
        super().close()
        self._flush()

    def _flush(self) -> None:
        text = " ".join("".join(self._parts).split())
        self._parts.clear()

        if text:
            self.paragraphs.append(text)


def extract_translation_paragraphs(
    source_format: TranslationSourceFormat,
    content: str,
) -> tuple[str, ...]:
    """Extract readable paragraphs without mutating the original source."""
    if source_format is TranslationSourceFormat.CLEANED_MARKDOWN:
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        return tuple(
            paragraph.strip()
            for paragraph in re.split(r"\n\s*\n", normalized)
            if paragraph.strip()
        )

    parser = _HTMLParagraphParser()
    parser.feed(content)
    parser.close()
    return tuple(parser.paragraphs)


def segment_translation_text(
    text: str,
    max_chars: int,
) -> tuple[str, ...]:
    """Split long paragraphs at readable boundaries while preserving order."""
    if max_chars < MIN_SEGMENT_CHARS:
        raise ValueError(
            f"max_chars must be at least {MIN_SEGMENT_CHARS}."
        )

    remaining = text.strip()
    segments: list[str] = []

    while len(remaining) > max_chars:
        window = remaining[: max_chars + 1]
        lower_bound = max_chars // 2
        boundary = max(
            (
                window.rfind(marker, lower_bound, max_chars + 1)
                for marker in ("。", "！", "？", ".", "!", "?", "\n", " ")
            ),
            default=-1,
        )
        cut = boundary + 1 if boundary >= lower_bound else max_chars
        segment = remaining[:cut].strip()

        if segment:
            segments.append(segment)

        remaining = remaining[cut:].strip()

    if remaining:
        segments.append(remaining)

    return tuple(segments)


class TranslationAgent:
    """Paragraph-preserving translation workflow with per-segment fallback."""

    def __init__(
        self,
        provider: LLMProvider,
        result_store: TranslationResultStore | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._provider = provider
        self._result_store = (
            result_store
            if result_store is not None
            else InMemoryTranslationResultStore()
        )
        self._clock = clock or (lambda: datetime.now(UTC))

    def translate(
        self,
        source: TranslationSource,
        options: TranslationOptions | None = None,
    ) -> TranslationResult:
        selected_options = options or TranslationOptions()
        selected_content = source.preferred_content()
        input_error = self._validate_input(
            source,
            selected_options,
            selected_content,
        )
        if input_error is not None:
            return input_error

        source_format, content = selected_content
        try:
            originals = extract_translation_paragraphs(source_format, content)
        except Exception:
            return self._failure_result(
                source,
                selected_options,
                source_format,
                (),
                TranslationErrorCode.INVALID_INPUT,
                "Article paragraphs could not be prepared for translation.",
            )
        if not originals:
            return self._failure_result(
                source,
                selected_options,
                source_format,
                (),
                TranslationErrorCode.INVALID_INPUT,
                "No readable article paragraphs are available for translation.",
            )

        if not self._provider.config.is_configured:
            paragraphs = tuple(
                self._failed_paragraph(
                    index,
                    original,
                    TranslationErrorCode.PROVIDER_NOT_CONFIGURED,
                    "AI Provider is not configured.",
                )
                for index, original in enumerate(originals)
            )
            return self._failure_result(
                source,
                selected_options,
                source_format,
                paragraphs,
                TranslationErrorCode.PROVIDER_NOT_CONFIGURED,
                "AI Provider is not configured.",
            )

        paragraphs = tuple(
            self._translate_paragraph(
                source,
                selected_options,
                index,
                original,
            )
            for index, original in enumerate(originals)
        )
        status = self._result_status(paragraphs)
        first_error = next(
            (
                paragraph
                for paragraph in paragraphs
                if paragraph.error_code is not None
            ),
            None,
        )
        result = TranslationResult(
            article_id=source.article_id,
            target_language=selected_options.target_language.strip(),
            paragraphs=paragraphs,
            source_format=source_format,
            generated_at=self._clock(),
            provider_model=self._provider.config.model,
            status=status,
            error_code=(
                first_error.error_code
                if status is TranslationStatus.FAILED and first_error
                else None
            ),
            error_message=(
                first_error.error_message
                if status is TranslationStatus.FAILED and first_error
                else ""
            ),
        )

        if not result.has_translations:
            return result

        saved_result = replace(result, is_saved=True)
        try:
            self._result_store.save(saved_result)
        except Exception:
            return replace(
                result,
                storage_error_code=TranslationErrorCode.STORAGE_FAILURE,
                storage_error_message=(
                    "The translation was generated but could not be saved locally."
                ),
            )

        return saved_result

    def build_request(
        self,
        source: TranslationSource,
        options: TranslationOptions,
        paragraph_index: int,
        segment_index: int,
        segment_count: int,
        text: str,
    ) -> LLMRequest:
        system_prompt = (
            options.custom_prompt.strip()
            or DEFAULT_TRANSLATION_SYSTEM_PROMPT
        )
        prompt = (
            f"Target language: {options.target_language.strip()}\n"
            f"Article title: {source.title.strip()}\n"
            f"Paragraph: {paragraph_index + 1}\n"
            f"Segment: {segment_index + 1}/{segment_count}\n\n"
            f"Text to translate:\n{text}"
        )
        return LLMRequest(prompt=prompt, system_prompt=system_prompt)

    def _translate_paragraph(
        self,
        source: TranslationSource,
        options: TranslationOptions,
        paragraph_index: int,
        original: str,
    ) -> TranslationParagraph:
        segments = segment_translation_text(
            original,
            options.max_segment_chars,
        )
        translations: list[str] = []
        first_error_code: TranslationErrorCode | None = None
        first_error_message = ""

        for segment_index, segment in enumerate(segments):
            request = self.build_request(
                source,
                options,
                paragraph_index,
                segment_index,
                len(segments),
                segment,
            )

            try:
                response = self._provider.complete(request)
            except LLMProviderError as exc:
                error_code = TranslationErrorCode.PROVIDER_FAILURE
                error_message = (
                    "Translation failed: "
                    f"{self._redact_api_key(str(exc))}"
                )
            except Exception:
                error_code = TranslationErrorCode.PROVIDER_FAILURE
                error_message = "Translation failed."
            else:
                translated = response.text.strip()
                if translated:
                    translations.append(translated)
                    continue

                error_code = TranslationErrorCode.EMPTY_RESPONSE
                error_message = "The Provider returned an empty translation."

            if first_error_code is None:
                first_error_code = error_code
                first_error_message = error_message

        translated_count = len(translations)
        if translated_count == len(segments):
            status = TranslationParagraphStatus.TRANSLATED
        elif translated_count:
            status = TranslationParagraphStatus.PARTIAL
        else:
            status = TranslationParagraphStatus.FAILED

        return TranslationParagraph(
            index=paragraph_index,
            original_text=original,
            translated_text=" ".join(translations),
            status=status,
            segment_count=len(segments),
            translated_segment_count=translated_count,
            error_code=first_error_code,
            error_message=first_error_message,
        )

    def _validate_input(
        self,
        source: TranslationSource,
        options: TranslationOptions,
        selected_content: tuple[TranslationSourceFormat, str] | None,
    ) -> TranslationResult | None:
        source_format = (
            selected_content[0]
            if selected_content is not None
            else TranslationSourceFormat.RAW_HTML
        )

        if not source.article_id.strip():
            return self._failure_result(
                source,
                options,
                source_format,
                (),
                TranslationErrorCode.INVALID_INPUT,
                "An article identifier is required for translation.",
            )

        if not options.target_language.strip():
            return self._failure_result(
                source,
                options,
                source_format,
                (),
                TranslationErrorCode.INVALID_INPUT,
                "A target language is required for translation.",
            )

        if not (
            MIN_SEGMENT_CHARS
            <= options.max_segment_chars
            <= MAX_SEGMENT_CHARS
        ):
            return self._failure_result(
                source,
                options,
                source_format,
                (),
                TranslationErrorCode.INVALID_INPUT,
                "Translation segment size is outside the supported range.",
            )

        if selected_content is None:
            return self._failure_result(
                source,
                options,
                source_format,
                (),
                TranslationErrorCode.INVALID_INPUT,
                "No readable article content is available for translation.",
            )

        return None

    def _failure_result(
        self,
        source: TranslationSource,
        options: TranslationOptions,
        source_format: TranslationSourceFormat,
        paragraphs: tuple[TranslationParagraph, ...],
        error_code: TranslationErrorCode,
        error_message: str,
    ) -> TranslationResult:
        return TranslationResult(
            article_id=source.article_id,
            target_language=options.target_language.strip(),
            paragraphs=paragraphs,
            source_format=source_format,
            generated_at=self._clock(),
            provider_model=self._provider.config.model,
            status=TranslationStatus.FAILED,
            error_code=error_code,
            error_message=error_message,
        )

    def _failed_paragraph(
        self,
        index: int,
        original: str,
        error_code: TranslationErrorCode,
        error_message: str,
    ) -> TranslationParagraph:
        return TranslationParagraph(
            index=index,
            original_text=original,
            translated_text="",
            status=TranslationParagraphStatus.FAILED,
            segment_count=1,
            translated_segment_count=0,
            error_code=error_code,
            error_message=error_message,
        )

    def _result_status(
        self,
        paragraphs: tuple[TranslationParagraph, ...],
    ) -> TranslationStatus:
        if all(
            paragraph.status is TranslationParagraphStatus.TRANSLATED
            for paragraph in paragraphs
        ):
            return TranslationStatus.COMPLETED

        if any(paragraph.has_translation for paragraph in paragraphs):
            return TranslationStatus.PARTIAL

        return TranslationStatus.FAILED

    def _redact_api_key(self, message: str) -> str:
        api_key = self._provider.config.api_key

        if not api_key:
            return message

        return message.replace(api_key, "••••")
