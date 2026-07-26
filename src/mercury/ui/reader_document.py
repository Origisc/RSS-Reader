from dataclasses import dataclass
from enum import Enum

from mercury.models.article import Article


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
        """Keep the RSS content stable while exposing processed results.

        ``original_html`` is the fetched web page used as the input for
        cleaning. Rendering that complete page inside the styled QTextBrowser
        changes the Original view after background processing and cannot
        reproduce the source site's CSS or scripts. Prefer the feed-provided
        content for this view and use fetched HTML only as a last-resort
        fallback.
        """
        return cls(
            raw_html=article.content_html or article.original_html,
            cleaned_html=article.cleaned_html or None,
            cleaned_markdown=article.cleaned_markdown or None,
            cleaning_error=article.clean_error,
        )

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
