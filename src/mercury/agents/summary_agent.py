from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from mercury.agents.translation_agent import (
    clean_translation_response,
    translation_matches_target_language,
)
from mercury.domain import (
    SummaryDetail,
    SummaryErrorCode,
    SummaryResult,
    SummarySourceFormat,
    SummaryStatus,
)
from mercury.llm import LLMProvider, LLMProviderError, LLMRequest


DEFAULT_SYSTEM_PROMPT = (
    "Create a faithful summary of the supplied article. "
    "Do not invent facts, links, quotations, or conclusions."
)

DETAIL_GUIDANCE = {
    SummaryDetail.BRIEF: "Use a compact overview with only the central point.",
    SummaryDetail.STANDARD: (
        "Cover the main argument and the most important supporting points."
    ),
    SummaryDetail.DETAILED: (
        "Provide a thorough structured summary that preserves important "
        "arguments, evidence, qualifications, and conclusions."
    ),
}

MAX_SUMMARY_ATTEMPTS = 3


@dataclass(frozen=True, slots=True)
class SummaryOptions:
    language: str = "Same as source"
    detail_level: SummaryDetail = SummaryDetail.STANDARD
    custom_prompt: str = ""


@dataclass(frozen=True, slots=True)
class SummarySource:
    article_id: str
    title: str
    raw_html: str
    cleaned_markdown: str | None = None
    cleaned_html: str | None = None

    def preferred_content(self) -> tuple[SummarySourceFormat, str] | None:
        candidates = (
            (
                SummarySourceFormat.CLEANED_MARKDOWN,
                self.cleaned_markdown,
            ),
            (SummarySourceFormat.CLEANED_HTML, self.cleaned_html),
            (SummarySourceFormat.RAW_HTML, self.raw_html),
        )

        for source_format, content in candidates:
            if content is not None and content.strip():
                return source_format, content.strip()

        return None


class SummaryResultStore(Protocol):
    """Persistence boundary implemented by Member A's local repository."""

    def save(self, result: SummaryResult) -> None:
        ...

    def latest_for_article(self, article_id: str) -> SummaryResult | None:
        ...


class InMemorySummaryResultStore:
    """Deterministic process-local store for Agent and UI development."""

    def __init__(self) -> None:
        self._results: dict[str, list[SummaryResult]] = {}

    def save(self, result: SummaryResult) -> None:
        self._results.setdefault(result.article_id, []).append(result)

    def latest_for_article(self, article_id: str) -> SummaryResult | None:
        results = self._results.get(article_id, [])

        if not results:
            return None

        return results[-1]


class SummaryAgent:
    """Provider-neutral summary workflow with a non-throwing failure result."""

    def __init__(
        self,
        provider: LLMProvider,
        result_store: SummaryResultStore | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._provider = provider
        self._result_store = (
            result_store
            if result_store is not None
            else InMemorySummaryResultStore()
        )
        self._clock = clock or (lambda: datetime.now(UTC))

    def summarize(
        self,
        source: SummarySource,
        options: SummaryOptions | None = None,
    ) -> SummaryResult:
        selected_options = options or SummaryOptions()
        selected_content = source.preferred_content()

        input_error = self._validate_input(
            source,
            selected_options,
            selected_content,
        )
        if input_error is not None:
            return input_error

        if not self._provider.config.is_configured:
            return self._failure_result(
                source,
                selected_options,
                selected_content[0],
                SummaryErrorCode.PROVIDER_NOT_CONFIGURED,
                "AI Provider is not configured.",
            )

        summary_text = ""
        previous_wrong_language_text = ""
        last_error_code = SummaryErrorCode.EMPTY_RESPONSE
        last_error_message = "The Provider returned an empty summary."

        for attempt in range(MAX_SUMMARY_ATTEMPTS):
            if attempt > 0 and previous_wrong_language_text:
                request = self.build_language_correction_request(
                    previous_wrong_language_text,
                    selected_options.language,
                )
            else:
                request = self.build_request(
                    source,
                    selected_options,
                    selected_content,
                    correction=attempt > 0,
                )

            try:
                response = self._provider.complete(request)
            except LLMProviderError as exc:
                message = self._redact_api_key(str(exc))
                return self._failure_result(
                    source,
                    selected_options,
                    selected_content[0],
                    SummaryErrorCode.PROVIDER_FAILURE,
                    f"Summary generation failed: {message}",
                )
            except Exception:
                return self._failure_result(
                    source,
                    selected_options,
                    selected_content[0],
                    SummaryErrorCode.PROVIDER_FAILURE,
                    "Summary generation failed.",
                )

            summary_text = clean_translation_response(response.text)
            if not summary_text:
                continue

            if translation_matches_target_language(
                summary_text,
                selected_options.language,
            ):
                break

            previous_wrong_language_text = summary_text
            summary_text = ""
            last_error_code = SummaryErrorCode.WRONG_LANGUAGE
            last_error_message = (
                "The Provider did not return the selected summary language "
                f"after {MAX_SUMMARY_ATTEMPTS} attempts."
            )

        if not summary_text:
            return self._failure_result(
                source,
                selected_options,
                selected_content[0],
                last_error_code,
                last_error_message,
            )

        result = SummaryResult(
            article_id=source.article_id,
            text=summary_text,
            language=selected_options.language.strip(),
            detail_level=selected_options.detail_level,
            source_format=selected_content[0],
            generated_at=self._clock(),
            provider_model=self._provider.config.model,
        )

        try:
            self._result_store.save(result)
        except Exception:
            return SummaryResult(
                article_id=result.article_id,
                text=result.text,
                language=result.language,
                detail_level=result.detail_level,
                source_format=result.source_format,
                generated_at=result.generated_at,
                provider_model=result.provider_model,
                status=SummaryStatus.GENERATED_NOT_SAVED,
                error_code=SummaryErrorCode.STORAGE_FAILURE,
                error_message=(
                    "The summary was generated but could not be saved locally."
                ),
            )

        return result

    def build_request(
        self,
        source: SummarySource,
        options: SummaryOptions,
        selected_content: tuple[SummarySourceFormat, str] | None = None,
        *,
        correction: bool = False,
    ) -> LLMRequest:
        content = selected_content or source.preferred_content()

        if content is None:
            raise ValueError("No readable article content is available.")

        source_format, article_content = content
        base_prompt = options.custom_prompt.strip() or DEFAULT_SYSTEM_PROMPT
        system_prompt = (
            f"{base_prompt}\n\n"
            "Mandatory output-language constraint (this overrides any "
            "conflicting language instruction above):\n"
            f"{_summary_language_requirement(options.language)}"
        )
        if correction:
            system_prompt = (
                f"{system_prompt}\n\n"
                "The previous answer used the wrong language or was empty. "
                "Regenerate the complete summary and obey the mandatory "
                "output-language constraint."
            )
        prompt = (
            f"Summary language: {options.language.strip()}\n"
            f"Detail level: {options.detail_level.value}\n"
            f"Detail guidance: {DETAIL_GUIDANCE[options.detail_level]}\n"
            f"Input format: {source_format.value}\n"
            f"Article title: {source.title.strip()}\n\n"
            f"Article content:\n{article_content}"
        )
        if correction:
            prompt = (
                "CORRECTION REQUIRED: return a complete replacement summary "
                f"entirely in {options.language.strip()}.\n\n{prompt}"
            )
        return LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0,
        )

    def build_language_correction_request(
        self,
        summary_text: str,
        language: str,
    ) -> LLMRequest:
        normalized = language.strip().casefold().replace("_", "-")
        if "chinese" in normalized or normalized.startswith("zh"):
            system_prompt = (
                "你是摘要语言校正器。必须把输入摘要完整改写为简体中文，"
                "保留原有事实、Markdown 结构、标题、列表、专有名词和限定条件。"
                "不得增加新事实，不得解释任务，不得输出英文开场或分析。"
                "只输出改写后的简体中文摘要。"
            )
            instruction = (
                "纠正要求：以下摘要使用了错误语言。请将其完整改写为简体中文，"
                "只返回简体中文摘要："
            )
        elif "english" in normalized or normalized.startswith("en"):
            system_prompt = (
                "You are a summary language corrector. Rewrite the supplied "
                "summary entirely in English while preserving its facts, "
                "Markdown structure, headings, lists, proper nouns, and "
                "qualifications. Add no facts or explanations. Return only "
                "the corrected English summary."
            )
            instruction = (
                "CORRECTION REQUIRED: rewrite the following summary entirely "
                "in English and return only the corrected summary:"
            )
        else:
            system_prompt = (
                "You are a summary language corrector. Preserve every fact "
                "and the Markdown structure. Return only the corrected "
                f"summary in {language.strip()}."
            )
            instruction = (
                "CORRECTION REQUIRED: rewrite the following summary entirely "
                f"in {language.strip()}:"
            )

        return LLMRequest(
            prompt=f"{instruction}\n\n{summary_text.strip()}",
            system_prompt=system_prompt,
            temperature=0,
        )

    def _validate_input(
        self,
        source: SummarySource,
        options: SummaryOptions,
        selected_content: tuple[SummarySourceFormat, str] | None,
    ) -> SummaryResult | None:
        if not source.article_id.strip():
            return self._failure_result(
                source,
                options,
                SummarySourceFormat.RAW_HTML,
                SummaryErrorCode.INVALID_INPUT,
                "An article identifier is required for summary generation.",
            )

        if not options.language.strip():
            source_format = (
                selected_content[0]
                if selected_content is not None
                else SummarySourceFormat.RAW_HTML
            )
            return self._failure_result(
                source,
                options,
                source_format,
                SummaryErrorCode.INVALID_INPUT,
                "A summary language is required.",
            )

        if selected_content is None:
            return self._failure_result(
                source,
                options,
                SummarySourceFormat.RAW_HTML,
                SummaryErrorCode.INVALID_INPUT,
                "No readable article content is available for summary.",
            )

        return None

    def _failure_result(
        self,
        source: SummarySource,
        options: SummaryOptions,
        source_format: SummarySourceFormat,
        error_code: SummaryErrorCode,
        error_message: str,
    ) -> SummaryResult:
        return SummaryResult(
            article_id=source.article_id,
            text="",
            language=options.language.strip(),
            detail_level=options.detail_level,
            source_format=source_format,
            generated_at=self._clock(),
            provider_model=self._provider.config.model,
            status=SummaryStatus.FAILED,
            error_code=error_code,
            error_message=error_message,
        )

    def _redact_api_key(self, message: str) -> str:
        api_key = self._provider.config.api_key

        if not api_key:
            return message

        return message.replace(api_key, "••••")


def _summary_language_requirement(language: str) -> str:
    normalized = language.strip().casefold().replace("_", "-")

    if "chinese" in normalized or normalized.startswith("zh"):
        return (
            "Write the entire summary in Simplified Chinese (简体中文), "
            "including headings, introductions, analysis, and conclusions. "
            "Use non-Chinese text only for unavoidable proper nouns, code, "
            "or quotations."
        )

    if "english" in normalized or normalized.startswith("en"):
        return (
            "Write the entire summary in English, including headings, "
            "introductions, analysis, and conclusions."
        )

    if normalized == "same as source":
        return (
            "Write the entire summary in the same language as the supplied "
            "article."
        )

    return f"Write the entire summary in {language.strip()}."
