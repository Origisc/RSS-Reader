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
        patterns = [
            r'<article[^>]*>(.*?)</article>',
            r'<main[^>]*>(.*?)</main>',
            r'<div[^>]*class=[\'"]?.*(post|content|article|entry).*[\'"]?[^>]*>(.*?)</div>',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, flags=re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1) if len(match.groups()) == 1 else match.group(2)

        body_match = re.search(r'<body[^>]*>(.*?)</body>', html, flags=re.DOTALL)
        if body_match:
            return body_match.group(1)

        return html

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
