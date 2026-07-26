from dataclasses import dataclass
from typing import Optional
from html.parser import HTMLParser


@dataclass
class CleanResult:
    success: bool
    cleaned_html: str = ""
    error_message: Optional[str] = None


class ReaderCleaner:
    def __init__(self):
        self._allowed_tags = {
            "h1", "h2", "h3", "h4", "h5", "h6",
            "p", "div", "span",
            "a", "img",
            "ul", "ol", "li",
            "table", "thead", "tbody", "tr", "th", "td",
            "pre", "code",
            "blockquote",
            "br", "hr",
            "strong", "em", "b", "i", "u",
            "article", "section", "main",
        }
        self._block_tags = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "ul", "ol", "table", "pre", "blockquote", "article", "section", "main", "br", "hr"}
        self._remove_attrs = {"style", "class", "id", "onclick", "onload", "onerror", "data-*"}

    def clean(self, html: str) -> CleanResult:
        if not html or not html.strip():
            return CleanResult(success=False, error_message="HTML content is empty")

        try:
            cleaned = self._remove_scripts_and_styles(html)
            cleaned = self._remove_comments(cleaned)
            cleaned = self._extract_main_content(cleaned)
            cleaned = self._normalise_legacy_prose_pre(cleaned)
            cleaned = self._sanitize_tags(cleaned)

            if not cleaned.strip():
                return CleanResult(success=False, error_message="Cleaned content is empty")

            return CleanResult(success=True, cleaned_html=cleaned)

        except Exception as e:
            return CleanResult(success=False, error_message=f"Cleaning failed: {str(e)}")

    def _remove_scripts_and_styles(self, html: str) -> str:
        import re
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        return html

    def _remove_comments(self, html: str) -> str:
        import re
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        return html

    def _extract_main_content(self, html: str) -> str:
        import re

        # Some older sites use one short ``article`` for a headline card and
        # another for the actual body. Returning the first regex match drops
        # the real article completely, so compare all semantic candidates.
        for tag in ("article", "main"):
            matches = re.findall(
                rf"<{tag}\b[^>]*>(.*?)</{tag}\s*>",
                html,
                flags=re.DOTALL | re.IGNORECASE,
            )
            if matches:
                return max(matches, key=self._content_score)

        content_divs = re.findall(
            (
                r"<div\b[^>]*class\s*=\s*"
                r"['\"][^'\"]*(?:post|content|article|entry)[^'\"]*['\"]"
                r"[^>]*>(.*?)</div\s*>"
            ),
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if content_divs:
            return max(content_divs, key=self._content_score)

        body_match = re.search(
            r"<body\b[^>]*>(.*?)</body\s*>",
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if body_match:
            return body_match.group(1)

        return html

    @staticmethod
    def _content_score(html_fragment: str) -> int:
        """Estimate useful candidate size without changing its HTML."""
        import re

        visible_text = re.sub(
            r"<[^>]+>",
            " ",
            html_fragment,
            flags=re.DOTALL,
        )
        return len(re.sub(r"\s+", " ", visible_text).strip())

    def _normalise_legacy_prose_pre(self, html: str) -> str:
        """Turn long prose stored in ``pre`` into readable HTML blocks."""
        import re
        from html import unescape

        def replace_pre(match) -> str:
            inner_html = match.group(1)
            if re.search(r"<\s*(?:code|kbd|samp)\b", inner_html, re.IGNORECASE):
                return match.group(0)

            text = unescape(inner_html).replace("\r\n", "\n").replace("\r", "\n")
            if not self._looks_like_prose_pre(text):
                return match.group(0)

            return self._prose_pre_to_html(text)

        return re.sub(
            r"<pre\b[^>]*>(.*?)</pre\s*>",
            replace_pre,
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )

    @staticmethod
    def _looks_like_prose_pre(text: str) -> bool:
        import re

        stripped = text.strip()
        if len(stripped) < 500:
            return False

        blocks = [
            block.strip()
            for block in re.split(r"\n\s*\n+", stripped)
            if block.strip()
        ]
        if len(blocks) < 3:
            return False

        wordy_blocks = sum(
            1
            for block in blocks
            if len(re.findall(r"\b[\w’'-]+\b", block, re.UNICODE)) >= 8
        )
        sentence_blocks = sum(
            1
            for block in blocks
            if re.search(r"[.!?。！？][\"'”’)]?\s*$", block)
        )
        has_setext_heading = bool(
            re.search(r"(?m)^[^\n]+\n(?:={3,}|-{3,})\s*$", stripped)
        )
        return wordy_blocks >= 3 and (
            has_setext_heading or sentence_blocks >= 3
        )

    @staticmethod
    def _prose_pre_to_html(text: str) -> str:
        import re
        from html import escape

        output: list[str] = []
        blocks = [
            block.strip()
            for block in re.split(r"\n\s*\n+", text.strip())
            if block.strip()
        ]

        for block in blocks:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                continue

            if len(lines) == 2 and re.fullmatch(r"={3,}", lines[1]):
                output.append(f"<h2>{escape(lines[0])}</h2>")
                continue

            if len(lines) == 2 and re.fullmatch(r"-{3,}", lines[1]):
                output.append(f"<h3>{escape(lines[0])}</h3>")
                continue

            if all(re.match(r"^[-*]\s+", line) for line in lines):
                items = "".join(
                    f"<li>{escape(re.sub(r'^[-*]\\s+', '', line))}</li>"
                    for line in lines
                )
                output.append(f"<ul>{items}</ul>")
                continue

            paragraph = " ".join(lines)
            output.append(f"<p>{escape(paragraph)}</p>")

        return "".join(output)

    def _sanitize_tags(self, html: str) -> str:
        class TagSanitizer(HTMLParser):
            def __init__(self, allowed_tags, block_tags, remove_attrs):
                super().__init__()
                self._allowed = allowed_tags
                self._block = block_tags
                self._remove = remove_attrs
                self.result = []

            def handle_starttag(self, tag, attrs):
                if tag.lower() not in self._allowed:
                    return

                cleaned_attrs = []
                for attr_name, attr_value in attrs:
                    if attr_name.lower() in self._remove:
                        continue
                    if attr_name.lower().startswith('data-'):
                        continue
                    cleaned_attrs.append(f'{attr_name}="{attr_value}"')

                attrs_str = ' '.join(cleaned_attrs)
                if attrs_str:
                    self.result.append(f'<{tag} {attrs_str}>')
                else:
                    self.result.append(f'<{tag}>')

                if tag.lower() in self._block:
                    self.result.append('\n')

            def handle_endtag(self, tag):
                if tag.lower() in self._allowed:
                    self.result.append(f'</{tag}>')
                    if tag.lower() in self._block:
                        self.result.append('\n')

            def handle_data(self, data):
                self.result.append(data)

            def handle_entityref(self, name):
                self.result.append(f'&{name};')

            def handle_charref(self, name):
                self.result.append(f'&#{name};')

        sanitizer = TagSanitizer(self._allowed_tags, self._block_tags, self._remove_attrs)
        sanitizer.feed(html)
        return ''.join(sanitizer.result).strip()
