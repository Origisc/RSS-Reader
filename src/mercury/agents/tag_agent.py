from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum

from mercury.llm import LLMProvider, LLMProviderError, LLMRequest


DEFAULT_TAG_SYSTEM_PROMPT = (
    "Suggest a small set of concise, reusable tags for the supplied article. "
    "Base every suggestion only on the article content. Prefer an existing "
    "tag when it accurately describes the article."
)
MAX_TAG_SUGGESTIONS = 8


class TagSuggestionErrorCode(str, Enum):
    INVALID_INPUT = "invalid_input"
    PROVIDER_NOT_CONFIGURED = "provider_not_configured"
    PROVIDER_FAILURE = "provider_failure"
    EMPTY_RESPONSE = "empty_response"


@dataclass(frozen=True, slots=True)
class TagSuggestionOptions:
    custom_prompt: str = ""
    max_suggestions: int = 5


@dataclass(frozen=True, slots=True)
class TagSource:
    article_id: str
    title: str
    raw_html: str
    cleaned_markdown: str | None = None
    cleaned_html: str | None = None
    existing_tags: tuple[str, ...] = ()
    assigned_tags: tuple[str, ...] = ()

    def preferred_content(self) -> tuple[str, str] | None:
        candidates = (
            ("cleaned_markdown", self.cleaned_markdown),
            ("cleaned_html", self.cleaned_html),
            ("raw_html", self.raw_html),
        )
        for source_format, content in candidates:
            if content is not None and content.strip():
                return source_format, content.strip()
        return None


@dataclass(frozen=True, slots=True)
class TagSuggestionResult:
    article_id: str
    suggestions: tuple[str, ...] = ()
    provider_model: str = ""
    error_code: TagSuggestionErrorCode | None = None
    error_message: str | None = None

    @property
    def has_suggestions(self) -> bool:
        return bool(self.suggestions)


class TagAgent:
    """Provider-neutral tag suggestions that never mutate local tags."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def suggest(
        self,
        source: TagSource,
        options: TagSuggestionOptions | None = None,
    ) -> TagSuggestionResult:
        selected_options = options or TagSuggestionOptions()
        content = source.preferred_content()
        input_error = self._validate_input(source, selected_options, content)
        if input_error is not None:
            return input_error

        if not self._provider.config.is_configured:
            return self._failure(
                source,
                TagSuggestionErrorCode.PROVIDER_NOT_CONFIGURED,
                "AI Provider is not configured.",
            )

        request = self.build_request(source, selected_options, content)
        try:
            response = self._provider.complete(request)
        except LLMProviderError as exc:
            return self._failure(
                source,
                TagSuggestionErrorCode.PROVIDER_FAILURE,
                self._redact_api_key(str(exc)),
            )
        except Exception:
            return self._failure(
                source,
                TagSuggestionErrorCode.PROVIDER_FAILURE,
                "Tag suggestion generation failed.",
            )

        suggestions = parse_tag_suggestions(
            response.text,
            max_suggestions=selected_options.max_suggestions,
            excluded_names=source.assigned_tags,
        )
        if not suggestions:
            return self._failure(
                source,
                TagSuggestionErrorCode.EMPTY_RESPONSE,
                "The Provider returned no usable tag suggestions.",
            )

        return TagSuggestionResult(
            article_id=source.article_id,
            suggestions=suggestions,
            provider_model=self._provider.config.model,
        )

    def build_request(
        self,
        source: TagSource,
        options: TagSuggestionOptions,
        selected_content: tuple[str, str] | None = None,
    ) -> LLMRequest:
        content = selected_content or source.preferred_content()
        if content is None:
            raise ValueError("No readable article content is available.")

        source_format, article_content = content
        custom_prompt = options.custom_prompt.strip()
        system_prompt = DEFAULT_TAG_SYSTEM_PROMPT
        if custom_prompt:
            system_prompt = (
                f"{system_prompt}\n\nAdditional user instructions:\n"
                f"{custom_prompt}"
            )
        system_prompt = (
            f"{system_prompt}\n\nMandatory output format: return only a JSON "
            "array of tag-name strings. Do not include Markdown, explanations, "
            "scores, or keys. Each tag must be at most 64 characters."
        )
        existing_tags = (
            json.dumps(source.existing_tags, ensure_ascii=False)
            if source.existing_tags
            else "[]"
        )
        assigned_tags = (
            json.dumps(source.assigned_tags, ensure_ascii=False)
            if source.assigned_tags
            else "[]"
        )
        prompt = (
            f"Maximum suggestions: {options.max_suggestions}\n"
            f"Existing local tags: {existing_tags}\n"
            f"Tags already assigned to this article: {assigned_tags}\n"
            f"Input format: {source_format}\n"
            f"Article title: {source.title.strip()}\n\n"
            f"Article content:\n{article_content}"
        )
        return LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
        )

    def _validate_input(
        self,
        source: TagSource,
        options: TagSuggestionOptions,
        content: tuple[str, str] | None,
    ) -> TagSuggestionResult | None:
        if not source.article_id.strip():
            return self._failure(
                source,
                TagSuggestionErrorCode.INVALID_INPUT,
                "An article identifier is required.",
            )
        if not 1 <= options.max_suggestions <= MAX_TAG_SUGGESTIONS:
            return self._failure(
                source,
                TagSuggestionErrorCode.INVALID_INPUT,
                f"Tag suggestion count must be between 1 and "
                f"{MAX_TAG_SUGGESTIONS}.",
            )
        if content is None:
            return self._failure(
                source,
                TagSuggestionErrorCode.INVALID_INPUT,
                "No readable article content is available.",
            )
        return None

    def _failure(
        self,
        source: TagSource,
        error_code: TagSuggestionErrorCode,
        error_message: str,
    ) -> TagSuggestionResult:
        return TagSuggestionResult(
            article_id=source.article_id,
            provider_model=self._provider.config.model,
            error_code=error_code,
            error_message=error_message,
        )

    def _redact_api_key(self, message: str) -> str:
        api_key = self._provider.config.api_key
        return message.replace(api_key, "••••") if api_key else message


def parse_tag_suggestions(
    response_text: str,
    *,
    max_suggestions: int = 5,
    excluded_names: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Parse strict JSON first, with a conservative plain-text fallback."""

    cleaned = response_text.strip()
    cleaned = re.sub(
        r"^\s*```(?:json)?\s*|\s*```\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    values: list[object] = []
    try:
        decoded = json.loads(cleaned)
    except (TypeError, ValueError, json.JSONDecodeError):
        decoded = None

    if isinstance(decoded, list):
        values = list(decoded)
    elif isinstance(decoded, dict) and isinstance(decoded.get("tags"), list):
        values = list(decoded["tags"])
    elif cleaned:
        values = re.split(r"[\n,，;；]+", cleaned)

    excluded = {
        _normalize_tag_name(name).casefold()
        for name in excluded_names
        if _normalize_tag_name(name)
    }
    suggestions: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        normalized = _normalize_tag_name(value)
        key = normalized.casefold()
        if (
            not normalized
            or len(normalized) > 64
            or key in excluded
            or key in seen
        ):
            continue
        suggestions.append(normalized)
        seen.add(key)
        if len(suggestions) >= max_suggestions:
            break
    return tuple(suggestions)


def _normalize_tag_name(value: str) -> str:
    without_bullet = re.sub(
        r"^\s*(?:[-*•]|\d+[.)])\s*",
        "",
        str(value),
    )
    return " ".join(without_bullet.strip(" \t\r\n`\"'#").split())
