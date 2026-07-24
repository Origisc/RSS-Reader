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
DEFAULT_SEGMENT_CHARS = 160
MAX_TRANSLATION_ATTEMPTS = 3
MAX_PARAGRAPH_FALLBACK_CHARS = 1_200

DEFAULT_TRANSLATION_SYSTEM_PROMPT = (
    "Translate the supplied article text faithfully. Preserve meaning, "
    "tone, names, technical terms, uncertainty, and line structure. "
    "Return only the translated text for the supplied segment. Do not include "
    "analysis, reasoning, notes, labels, quotation wrappers, or the source "
    "text."
)
_LEADING_THINK_BLOCK = re.compile(
    r"^\s*<think\b[^>]*>.*?</think>\s*",
    flags=re.IGNORECASE | re.DOTALL,
)
_HAN_CHARACTER = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
_LATIN_LETTER = re.compile(r"[A-Za-z]")
_URL_ONLY = re.compile(r"https?://\S+\Z", flags=re.IGNORECASE)


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
        # Reader HTML is the preferred translation source because the same
        # p/ul/ol segment boundaries can be reused when translations are
        # inserted back into the article. Markdown remains the fallback when
        # cleaned HTML is unavailable.
        candidates = (
            (TranslationSourceFormat.CLEANED_HTML, self.cleaned_html),
            (
                TranslationSourceFormat.CLEANED_MARKDOWN,
                self.cleaned_markdown,
            ),
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
    """Extract the same Reader blocks used by bilingual HTML rendering."""

    _TRANSLATABLE_TAGS = {"p", "ul", "ol"}
    _IGNORED_TAGS = {"script", "style"}
    _VOID_TAGS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paragraphs: list[str] = []
        self._parts: list[str] = []
        self._ignored_depth = 0
        self._candidate_tag: str | None = None
        self._candidate_nesting = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        lowered = tag.lower()
        if lowered in self._IGNORED_TAGS:
            self._ignored_depth += 1
            return

        if self._ignored_depth:
            return

        if self._candidate_tag is not None:
            if lowered == "br":
                self._parts.append("\n")
            elif lowered in {"li", "td", "th"} and self._parts:
                self._parts.append(" ")
            if lowered not in self._VOID_TAGS:
                self._candidate_nesting += 1
            return

        if lowered in self._TRANSLATABLE_TAGS:
            self._candidate_tag = lowered
            self._candidate_nesting = 0
            self._parts.clear()

    def handle_startendtag(self, tag: str, attrs) -> None:
        if (
            not self._ignored_depth
            and self._candidate_tag is not None
            and tag.lower() == "br"
        ):
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in self._IGNORED_TAGS:
            self._ignored_depth = max(0, self._ignored_depth - 1)
            return

        if self._ignored_depth:
            return

        if self._candidate_tag is None:
            return

        if (
            lowered == self._candidate_tag
            and self._candidate_nesting == 0
        ):
            self._flush()
            return

        if lowered in {"li", "td", "th"}:
            self._parts.append(" ")
        if lowered not in self._VOID_TAGS and self._candidate_nesting:
            self._candidate_nesting -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth and self._candidate_tag is not None:
            self._parts.append(data)

    def close(self) -> None:
        super().close()
        if self._candidate_tag is not None:
            self._flush()

    def _flush(self) -> None:
        text = " ".join("".join(self._parts).split())
        self._parts.clear()
        self._candidate_tag = None
        self._candidate_nesting = 0

        if text:
            self.paragraphs.append(text)


class _HTMLFallbackParagraphParser(HTMLParser):
    """Recover paragraphs from legacy RSS fragments separated by br tags."""

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
        self._parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        lowered = tag.lower()
        if lowered in self._IGNORED_TAGS:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if lowered == "br":
            self._parts.append("\n")
        elif lowered in self._BLOCK_TAGS:
            self._parts.append("\n\n")

    def handle_startendtag(self, tag: str, attrs) -> None:
        if not self._ignored_depth and tag.lower() == "br":
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in self._IGNORED_TAGS:
            self._ignored_depth = max(0, self._ignored_depth - 1)
            return
        if not self._ignored_depth and lowered in self._BLOCK_TAGS:
            self._parts.append("\n\n")

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self._parts.append(data)

    @property
    def paragraphs(self) -> tuple[str, ...]:
        normalized = (
            "".join(self._parts)
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .replace("\u2028", "\n")
            .replace("\u2029", "\n\n")
        )
        return tuple(
            " ".join(paragraph.split())
            for paragraph in re.split(r"\n\s*\n", normalized)
            if paragraph.strip()
        )


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

    fallback_parser = _HTMLFallbackParagraphParser()
    fallback_parser.feed(content)
    fallback_parser.close()
    fallback_paragraphs = fallback_parser.paragraphs
    structured_paragraphs = tuple(parser.paragraphs)

    if not structured_paragraphs:
        return fallback_paragraphs

    # Some legacy RSS entries contain a long body separated only by <br><br>,
    # followed by one valid <p> (commonly an appended source link). Looking
    # only at p/ul/ol would then discard the complete body and translate just
    # that final block. Prefer the fallback only when it recovers both more
    # paragraphs and substantially more readable text.
    if source_format is TranslationSourceFormat.RAW_HTML:
        structured_chars = sum(map(len, structured_paragraphs))
        fallback_chars = sum(map(len, fallback_paragraphs))
        if (
            len(fallback_paragraphs) > len(structured_paragraphs)
            and fallback_chars > max(structured_chars * 2, structured_chars + 20)
        ):
            return fallback_paragraphs

    return structured_paragraphs


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
        sentence_lower_bound = max_chars // 4
        sentence_boundary = max(
            (
                window.rfind(
                    marker,
                    sentence_lower_bound,
                    max_chars + 1,
                )
                for marker in ("。", "！", "？", ".", "!", "?", "\n")
            ),
            default=-1,
        )
        if sentence_boundary >= sentence_lower_bound:
            cut = sentence_boundary + 1
        else:
            clause_lower_bound = max_chars // 2
            clause_boundary = max(
                (
                    window.rfind(
                        marker,
                        clause_lower_bound,
                        max_chars + 1,
                    )
                    for marker in ("；", "：", "，", ";", ":", ",", " ")
                ),
                default=-1,
            )
            cut = (
                clause_boundary + 1
                if clause_boundary >= clause_lower_bound
                else max_chars
            )
        segment = remaining[:cut].strip()

        if segment:
            segments.append(segment)

        remaining = remaining[cut:].strip()

    if remaining:
        segments.append(remaining)

    minimum_tail_chars = max(MIN_SEGMENT_CHARS, max_chars // 4)
    if (
        max_chars >= 80
        and len(segments) > 1
        and len(segments[-1]) < minimum_tail_chars
    ):
        segments[-2] = f"{segments[-2]} {segments[-1]}"
        segments.pop()

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
        progress_callback: Callable[[TranslationResult], None] | None = None,
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

        completed_paragraphs: list[TranslationParagraph] = []
        for index, original in enumerate(originals):
            completed_paragraphs.append(
                self._translate_paragraph(
                    source,
                    selected_options,
                    index,
                    original,
                )
            )
            if progress_callback is not None:
                progress_paragraphs = tuple(completed_paragraphs) + tuple(
                    self._pending_paragraph(
                        pending_index,
                        pending_original,
                    )
                    for pending_index, pending_original in enumerate(
                        originals[len(completed_paragraphs) :],
                        start=len(completed_paragraphs),
                    )
                )
                progress_result = TranslationResult(
                    article_id=source.article_id,
                    target_language=selected_options.target_language.strip(),
                    paragraphs=progress_paragraphs,
                    source_format=source_format,
                    generated_at=self._clock(),
                    provider_model=self._provider.config.model,
                    status=TranslationStatus.PARTIAL,
                )
                try:
                    progress_callback(progress_result)
                except Exception:
                    # Presentation progress must never break translation.
                    pass

        paragraphs = tuple(completed_paragraphs)
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
        *,
        correction: bool = False,
    ) -> LLMRequest:
        custom_prompt = options.custom_prompt.strip()
        system_prompt = DEFAULT_TRANSLATION_SYSTEM_PROMPT
        if custom_prompt:
            system_prompt = (
                f"{system_prompt}\n\nAdditional user instructions:\n"
                f"{custom_prompt}"
            )
        if _is_chinese_target(options.target_language):
            system_prompt = (
                f"{system_prompt}\n\n"
                "你是逐句翻译器。必须把输入中的每一句、每个从句完整翻译成"
                "简体中文，保留编号、引用、专有名词和技术术语。只输出译文，"
                "不得输出翻译说明、任务描述、英文改写、摘要或遗漏内容。"
            )
        if correction:
            system_prompt = (
                f"{system_prompt}\n\n"
                "The previous answer was invalid, used the wrong language, "
                "or omitted part of the source. Translate every sentence and "
                "clause in the supplied segment. "
                f"Output the complete translation entirely in "
                f"{options.target_language.strip()}. Do not summarize, omit, "
                "paraphrase in the source language, explain, or include the "
                "source text."
            )
        prompt = (
            f"Target language: {options.target_language.strip()}\n"
            f"Article title: {source.title.strip()}\n"
            f"Paragraph: {paragraph_index + 1}\n"
            f"Segment: {segment_index + 1}/{segment_count}\n\n"
            "Return only this segment's target-language translation. "
            "Do not repeat the source segment.\n\n"
            f"Text to translate:\n{text}"
        )
        if correction:
            prompt = (
                "CORRECTION REQUIRED: the previous response was in the wrong "
                "language or did not translate the complete source segment. "
                "Translate all content from beginning to end, including text "
                "after conjunctions and citations. Return only the complete "
                f"{options.target_language.strip()} translation.\n\n"
                f"{prompt}"
            )
        return LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0,
        )

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
            translated, error_code, error_message = self._translate_segment(
                source,
                options,
                paragraph_index,
                segment_index,
                len(segments),
                segment,
            )
            if translated:
                translations.append(translated)
                continue

            if first_error_code is None:
                first_error_code = error_code
                first_error_message = error_message

        validation_errors = {
            TranslationErrorCode.EMPTY_RESPONSE,
            TranslationErrorCode.WRONG_LANGUAGE,
            TranslationErrorCode.INCOMPLETE_RESPONSE,
        }
        if (
            len(segments) > 1
            and first_error_code in validation_errors
            and len(original) <= MAX_PARAGRAPH_FALLBACK_CHARS
        ):
            recovered, recovery_error, recovery_message = (
                self._translate_segment(
                    source,
                    options,
                    paragraph_index,
                    0,
                    1,
                    original,
                )
            )
            if recovered:
                return TranslationParagraph(
                    index=paragraph_index,
                    original_text=original,
                    translated_text=recovered,
                    status=TranslationParagraphStatus.TRANSLATED,
                    segment_count=1,
                    translated_segment_count=1,
                )
            if not translations:
                first_error_code = recovery_error
                first_error_message = recovery_message

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

    def _translate_segment(
        self,
        source: TranslationSource,
        options: TranslationOptions,
        paragraph_index: int,
        segment_index: int,
        segment_count: int,
        segment: str,
    ) -> tuple[str, TranslationErrorCode | None, str]:
        last_error_code = TranslationErrorCode.EMPTY_RESPONSE
        last_error_message = "The Provider returned an empty translation."

        for attempt in range(MAX_TRANSLATION_ATTEMPTS):
            request = self.build_request(
                source,
                options,
                paragraph_index,
                segment_index,
                segment_count,
                segment,
                correction=attempt > 0,
            )
            try:
                response = self._provider.complete(request)
            except LLMProviderError as exc:
                return (
                    "",
                    TranslationErrorCode.PROVIDER_FAILURE,
                    "Translation failed: "
                    f"{self._redact_api_key(str(exc))}",
                )
            except Exception:
                return (
                    "",
                    TranslationErrorCode.PROVIDER_FAILURE,
                    "Translation failed.",
                )

            translated = clean_translation_response(response.text)
            if not translated:
                last_error_code = TranslationErrorCode.EMPTY_RESPONSE
                last_error_message = (
                    "The Provider returned an empty translation."
                )
                continue

            validation_error = translation_validation_error(
                translated,
                options.target_language,
                segment,
            )
            if validation_error is None:
                return translated, None, ""

            last_error_code = validation_error
            if validation_error is TranslationErrorCode.WRONG_LANGUAGE:
                last_error_message = (
                    "The Provider did not return the requested target language "
                    f"after {MAX_TRANSLATION_ATTEMPTS} attempts."
                )
            else:
                last_error_message = (
                    "The Provider omitted part of the source or returned "
                    "instructions instead of a translation after "
                    f"{MAX_TRANSLATION_ATTEMPTS} attempts."
                )

        return "", last_error_code, last_error_message

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

    def _pending_paragraph(
        self,
        index: int,
        original: str,
    ) -> TranslationParagraph:
        return TranslationParagraph(
            index=index,
            original_text=original,
            translated_text="",
            status=TranslationParagraphStatus.PARTIAL,
            segment_count=1,
            translated_segment_count=0,
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


def clean_translation_response(text: str) -> str:
    """Remove leading model reasoning blocks while retaining translated text."""
    cleaned = text.strip().lstrip("\ufeff")
    while True:
        without_thinking = _LEADING_THINK_BLOCK.sub("", cleaned, count=1)
        if without_thinking == cleaned:
            return cleaned.strip()
        cleaned = without_thinking


def translation_matches_target_language(
    translated_text: str,
    target_language: str,
    source_text: str = "",
) -> bool:
    """Reject obvious source-language paraphrases for supported UI targets."""
    translated = translated_text.strip()
    if not translated:
        return False

    source = source_text.strip()
    if _URL_ONLY.fullmatch(source):
        return True
    if (
        translated.casefold() == source.casefold()
        and len(source.split()) <= 2
    ):
        return True

    normalized_target = target_language.strip().casefold().replace("_", "-")
    han_count = len(_HAN_CHARACTER.findall(translated))
    latin_count = len(_LATIN_LETTER.findall(translated))
    letter_count = han_count + latin_count

    if _is_chinese_target(normalized_target):
        return (
            han_count >= 2
            and han_count / max(1, letter_count) >= 0.15
        )

    if "english" in normalized_target or normalized_target.startswith("en"):
        return (
            latin_count >= 2
            and latin_count / max(1, letter_count) >= 0.5
        )

    # The UI currently exposes Chinese and English. Other user-supplied target
    # names remain provider-neutral and are not rejected without a reliable
    # local script detector.
    return True


def translation_appears_complete(
    translated_text: str,
    target_language: str,
    source_text: str,
) -> bool:
    """Reject translations that are far too short to cover a source segment."""
    source = source_text.strip()
    translated = translated_text.strip()
    if not source or _URL_ONLY.fullmatch(source):
        return True

    compact_source = "".join(source.split())
    compact_translation = "".join(translated.split())
    if len(compact_source) < 80:
        return True

    normalized_target = target_language.strip().casefold().replace("_", "-")
    source_han = len(_HAN_CHARACTER.findall(source))
    source_latin = len(_LATIN_LETTER.findall(source))
    chinese_target = _is_chinese_target(normalized_target)
    minimum_ratio = (
        0.20
        if chinese_target and source_latin > source_han
        else 0.35
    )
    return (
        len(compact_translation) / max(1, len(compact_source))
        >= minimum_ratio
    )


def translation_validation_error(
    translated_text: str,
    target_language: str,
    source_text: str,
) -> TranslationErrorCode | None:
    if not translation_matches_target_language(
        translated_text,
        target_language,
        source_text,
    ):
        return TranslationErrorCode.WRONG_LANGUAGE
    if _looks_like_translation_instruction(
        translated_text,
        target_language,
        source_text,
    ):
        return TranslationErrorCode.INCOMPLETE_RESPONSE
    if not translation_appears_complete(
        translated_text,
        target_language,
        source_text,
    ):
        return TranslationErrorCode.INCOMPLETE_RESPONSE
    return None


def _is_chinese_target(target_language: str) -> bool:
    normalized = target_language.strip().casefold().replace("_", "-")
    return "chinese" in normalized or normalized.startswith("zh")


def _looks_like_translation_instruction(
    translated_text: str,
    target_language: str,
    source_text: str,
) -> bool:
    if not _is_chinese_target(target_language):
        return False

    source_lower = source_text.casefold()
    if "translate" in source_lower or "translation" in source_lower:
        return False

    instruction_markers = (
        "翻译为简体中文",
        "翻译成简体中文",
        "翻译如下",
        "以下是译文",
        "应准确传达原意",
        "需要准确翻译",
    )
    return any(marker in translated_text for marker in instruction_markers)
