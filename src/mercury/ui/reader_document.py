import re
from dataclasses import dataclass
from enum import Enum
from html import unescape

from mercury.models.article import Article


_INLINE_STYLE_PATTERN = re.compile(
    r"(?P<prefix>\s+style\s*=\s*)(?P<quote>[\"'])"
    r"(?P<style>.*?)(?P=quote)",
    re.IGNORECASE | re.DOTALL,
)
_THEME_STYLE_DECLARATION_PATTERN = re.compile(
    r"(?<![-\w])(?:background(?:-color|-image)?|color)"
    r"\s*:\s*[^;]*(?:;|$)",
    re.IGNORECASE,
)
_THEME_HTML_ATTRIBUTE_PATTERN = re.compile(
    r"\s+(?:bgcolor|background|text|link|vlink|alink)\s*=\s*"
    r"(?:[\"'][^\"']*[\"']|[^\s>]+)",
    re.IGNORECASE,
)


class ReaderView(str, Enum):
    """Article representations that the reader UI can display."""

    RAW = "raw"
    CLEANED_HTML = "cleaned_html"
    MARKDOWN = "markdown"


class ReaderContentFormat(str, Enum):
    HTML = "html"
    MARKDOWN = "markdown"


@dataclass(frozen=True, slots=True)
class ResolvedReaderContent:
    content: str
    content_format: ReaderContentFormat
    used_fallback: bool = False


@dataclass(frozen=True, slots=True)
class ReaderDocument:
    """Structured ReaderService result consumed only for presentation."""

    raw_html: str
    cleaned_html: str | None = None
    cleaned_markdown: str | None = None
    cleaning_error: str | None = None

    @classmethod
    def from_article(cls, article: Article) -> "ReaderDocument":
        """Expose the most complete safe local source for each Reader view.

        Feed descriptions are often only excerpts. Once a page fetch succeeds,
        prefer its cached HTML when it contains substantially more visible
        content. A short JavaScript shell or error page must not replace a more
        useful Feed body, and failed or pending fetches keep the Feed fallback.
        """
        return cls(
            raw_html=cls._raw_html_for(article),
            cleaned_html=article.cleaned_html or None,
            cleaned_markdown=article.cleaned_markdown or None,
            cleaning_error=article.clean_error,
        )

    @classmethod
    def _raw_html_for(cls, article: Article) -> str:
        feed_html = article.content_html or ""
        fetched_html = article.original_html or ""
        fetched_display_html = cls._fetched_display_html(article)

        if not feed_html:
            return fetched_display_html
        if not fetched_html or article.fetch_status != "success":
            return feed_html

        feed_length = cls._visible_text_length(feed_html)
        complete_length = cls._visible_text_length(fetched_display_html)

        minimum_gain = max(100, round(feed_length * 0.25))
        if complete_length - feed_length >= minimum_gain:
            return fetched_display_html
        return feed_html

    @classmethod
    def _fetched_display_html(cls, article: Article) -> str:
        """Return fetched content without embedding a source website shell."""
        fetched_html = article.original_html or ""
        if not fetched_html:
            return ""

        if not cls._is_complete_document(fetched_html):
            return cls.prepare_for_embedding(fetched_html)

        if article.cleaned_html:
            return article.cleaned_html

        semantic_fragment = cls._largest_semantic_fragment(fetched_html)
        return cls.prepare_for_embedding(
            semantic_fragment or fetched_html
        )

    @staticmethod
    def _is_complete_document(html: str) -> bool:
        return bool(
            re.search(
                r"<!doctype\b|<html\b|<head\b|<body\b",
                html,
                flags=re.IGNORECASE,
            )
        )

    @classmethod
    def _largest_semantic_fragment(cls, html: str) -> str:
        for tag in ("article", "main"):
            candidates = re.findall(
                rf"<{tag}\b[^>]*>.*?</{tag}\s*>",
                html,
                flags=re.IGNORECASE | re.DOTALL,
            )
            if candidates:
                return max(candidates, key=cls._visible_text_length)
        return ""

    @staticmethod
    def prepare_for_embedding(html: str) -> str:
        """Keep semantic HTML while dropping page-level theme overrides."""
        safe_html = re.sub(
            r"<head\b[^>]*>.*?</head\s*>",
            "",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        safe_html = re.sub(
            r"<(?:script|style|noscript)\b[^>]*>.*?"
            r"</(?:script|style|noscript)\s*>",
            "",
            safe_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        safe_html = re.sub(
            r"<!doctype[^>]*>|</?(?:html|body)\b[^>]*>",
            "",
            safe_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        safe_html = re.sub(
            r"<title\b[^>]*>.*?</title\s*>",
            "",
            safe_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        safe_html = re.sub(
            r"<(?:base|link|meta)\b[^>]*>",
            "",
            safe_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        safe_html = _THEME_HTML_ATTRIBUTE_PATTERN.sub("", safe_html)

        def remove_theme_style(match: re.Match[str]) -> str:
            style = _THEME_STYLE_DECLARATION_PATTERN.sub(
                "",
                match.group("style"),
            )
            style = re.sub(r";{2,}", ";", style).strip(" ;")
            if not style:
                return ""
            quote = match.group("quote")
            return (
                f"{match.group('prefix')}{quote}"
                f"{style};{quote}"
            )

        safe_html = _INLINE_STYLE_PATTERN.sub(
            remove_theme_style,
            safe_html,
        )
        return safe_html.strip()

    @staticmethod
    def _visible_text_length(html: str) -> int:
        without_non_content = re.sub(
            r"<(?:script|style|noscript)\b[^>]*>.*?"
            r"</(?:script|style|noscript)\s*>",
            " ",
            html or "",
            flags=re.IGNORECASE | re.DOTALL,
        )
        visible_text = re.sub(
            r"<[^>]+>",
            " ",
            without_non_content,
            flags=re.DOTALL,
        )
        return len(" ".join(unescape(visible_text).split()))

    def resolve(self, view: ReaderView) -> ResolvedReaderContent:
        """Resolve a requested view, falling back to the original HTML."""
        if view is ReaderView.RAW:
            return ResolvedReaderContent(
                content=self.raw_html,
                content_format=ReaderContentFormat.HTML,
            )

        if view is ReaderView.CLEANED_HTML and self.cleaned_html is not None:
            return ResolvedReaderContent(
                content=self.cleaned_html,
                content_format=ReaderContentFormat.HTML,
            )

        if view is ReaderView.MARKDOWN and self.cleaned_markdown is not None:
            return ResolvedReaderContent(
                content=self.cleaned_markdown,
                content_format=ReaderContentFormat.MARKDOWN,
            )

        return ResolvedReaderContent(
            content=self.raw_html,
            content_format=ReaderContentFormat.HTML,
            used_fallback=True,
        )
