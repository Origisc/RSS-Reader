from dataclasses import dataclass
from html import escape, unescape
from html.parser import HTMLParser

from mercury.domain import (
    TranslationParagraph,
    TranslationParagraphStatus,
)


_TRANSLATABLE_TAGS = {"p", "ul", "ol"}
_IGNORED_TEXT_TAGS = {"script", "style"}
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


@dataclass(frozen=True, slots=True)
class InterleavedHTML:
    """Original HTML with paragraph translations inserted in source order."""

    html: str
    inserted_count: int
    expected_count: int
    alignment_failed: bool

    @property
    def fully_aligned(self) -> bool:
        return (
            not self.alignment_failed
            and self.inserted_count == self.expected_count
        )


def translation_card_html(
    paragraph: TranslationParagraph,
    unavailable_text: str,
    translating_text: str = "",
) -> str:
    if (
        not paragraph.translated_text.strip()
        and paragraph.status is TranslationParagraphStatus.PARTIAL
        and paragraph.translated_segment_count == 0
    ):
        translated_text = translating_text or unavailable_text
    else:
        translated_text = (
            paragraph.translated_text.strip()
            if paragraph.translated_text.strip()
            else unavailable_text
        )
    classes = ["translation-block"]
    if paragraph.status is TranslationParagraphStatus.FAILED:
        classes.append("translation-unavailable")
    elif paragraph.status is TranslationParagraphStatus.PARTIAL:
        classes.append("translation-partial")

    safe_translation = escape(translated_text).replace("\n", "<br>")
    return (
        f'<div class="{" ".join(classes)}">'
        f"<p>{safe_translation}</p>"
        "</div>"
    )


class _HTMLTranslationInterleaver(HTMLParser):
    def __init__(
        self,
        paragraphs: tuple[TranslationParagraph, ...],
        unavailable_text: str,
        translating_text: str = "",
    ) -> None:
        super().__init__(convert_charrefs=False)
        self._paragraphs = paragraphs
        self._unavailable_text = unavailable_text
        self._translating_text = translating_text
        self._paragraph_index = 0
        self._output: list[str] = []
        self._parts: list[str] = []
        self._ignored_depth = 0
        self._candidate_tag: str | None = None
        self._candidate_nesting = 0
        self.alignment_failed = False

    @property
    def html(self) -> str:
        return "".join(self._output)

    @property
    def inserted_count(self) -> int:
        return self._paragraph_index

    def handle_starttag(self, tag: str, attrs) -> None:
        lowered = tag.lower()
        raw_tag = self.get_starttag_text() or self._start_tag(tag, attrs)
        self._output.append(raw_tag)

        if lowered in _IGNORED_TEXT_TAGS:
            self._ignored_depth += 1
            return

        if self._ignored_depth:
            return

        if self._candidate_tag is not None:
            if lowered == "br":
                self._parts.append("\n")
            elif lowered in {"li", "td", "th"} and self._parts:
                self._parts.append(" ")
            if lowered not in _VOID_TAGS:
                self._candidate_nesting += 1
            return

        if lowered in _TRANSLATABLE_TAGS:
            self._candidate_tag = lowered
            self._candidate_nesting = 0
            self._parts.clear()

    def handle_startendtag(self, tag: str, attrs) -> None:
        lowered = tag.lower()
        raw_tag = self.get_starttag_text() or self._start_tag(
            tag,
            attrs,
            closed=True,
        )
        self._output.append(raw_tag)
        if (
            not self._ignored_depth
            and self._candidate_tag is not None
            and lowered == "br"
        ):
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        self._output.append(f"</{tag}>")

        if lowered in _IGNORED_TEXT_TAGS:
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
            self._append_translation(self._consume_candidate_translation())
            return

        if lowered in {"li", "td", "th"}:
            self._parts.append(" ")
        if lowered not in _VOID_TAGS and self._candidate_nesting:
            self._candidate_nesting -= 1

    def handle_data(self, data: str) -> None:
        self._output.append(data)
        if not self._ignored_depth and self._candidate_tag is not None:
            self._parts.append(data)

    def handle_entityref(self, name: str) -> None:
        value = f"&{name};"
        self._output.append(value)
        if not self._ignored_depth and self._candidate_tag is not None:
            self._parts.append(unescape(value))

    def handle_charref(self, name: str) -> None:
        value = f"&#{name};"
        self._output.append(value)
        if not self._ignored_depth and self._candidate_tag is not None:
            self._parts.append(unescape(value))

    def handle_comment(self, data: str) -> None:
        self._output.append(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        self._output.append(f"<!{decl}>")

    def handle_pi(self, data: str) -> None:
        self._output.append(f"<?{data}>")

    def finish(self) -> None:
        if self._candidate_tag is not None:
            self.alignment_failed = True
            self._reset_candidate()
        if self._paragraph_index != len(self._paragraphs):
            self.alignment_failed = True

    def _consume_candidate_translation(self) -> str:
        original_text = _normalize_text("".join(self._parts))
        self._reset_candidate()
        if not original_text:
            return ""

        if self._paragraph_index >= len(self._paragraphs):
            self.alignment_failed = True
            return ""

        paragraph = self._paragraphs[self._paragraph_index]
        if original_text != _normalize_text(paragraph.original_text):
            self.alignment_failed = True
            return ""

        self._paragraph_index += 1
        return translation_card_html(paragraph, self._unavailable_text, self._translating_text)

    def _reset_candidate(self) -> None:
        self._parts.clear()
        self._candidate_tag = None
        self._candidate_nesting = 0

    def _append_translation(self, translation: str) -> None:
        if translation:
            self._output.append(translation)

    @staticmethod
    def _start_tag(
        tag: str,
        attrs,
        *,
        closed: bool = False,
    ) -> str:
        rendered_attrs = "".join(
            f' {name}="{escape(value or "", quote=True)}"'
            for name, value in attrs
        )
        ending = " />" if closed else ">"
        return f"<{tag}{rendered_attrs}{ending}"


def interleave_html_translations(
    source_html: str,
    paragraphs: tuple[TranslationParagraph, ...],
    unavailable_text: str,
    translating_text: str = "",
) -> InterleavedHTML:
    """Preserve source markup and insert each translation after its block."""
    ordered_paragraphs = tuple(
        sorted(paragraphs, key=lambda paragraph: paragraph.index)
    )
    expected_indexes = tuple(range(len(ordered_paragraphs)))
    actual_indexes = tuple(
        paragraph.index for paragraph in ordered_paragraphs
    )
    if actual_indexes != expected_indexes:
        return InterleavedHTML(
            html=source_html,
            inserted_count=0,
            expected_count=len(paragraphs),
            alignment_failed=True,
        )

    parser = _HTMLTranslationInterleaver(
        ordered_paragraphs,
        unavailable_text,
        translating_text,
    )
    try:
        parser.feed(source_html)
        parser.close()
        parser.finish()
    except Exception:
        return InterleavedHTML(
            html=source_html,
            inserted_count=parser.inserted_count,
            expected_count=len(paragraphs),
            alignment_failed=True,
        )

    return InterleavedHTML(
        html=parser.html,
        inserted_count=parser.inserted_count,
        expected_count=len(paragraphs),
        alignment_failed=parser.alignment_failed,
    )


def _normalize_text(text: str) -> str:
    return " ".join(text.split())
