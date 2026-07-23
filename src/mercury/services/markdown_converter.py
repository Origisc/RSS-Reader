from dataclasses import dataclass
from typing import Optional
from html.parser import HTMLParser


@dataclass
class ConvertResult:
    success: bool
    markdown: str = ""
    error_message: Optional[str] = None


class MarkdownConverter:
    def __init__(self):
        self._heading_map = {
            'h1': '#',
            'h2': '##',
            'h3': '###',
            'h4': '####',
            'h5': '#####',
            'h6': '######',
        }

    def convert(self, html: str) -> ConvertResult:
        if not html or not html.strip():
            return ConvertResult(success=False, error_message="HTML content is empty")

        try:
            converter = _HTMLToMarkdownParser(self._heading_map)
            converter.feed(html)
            markdown = converter.get_result()

            if not markdown.strip():
                return ConvertResult(success=False, error_message="Converted Markdown is empty")

            return ConvertResult(success=True, markdown=markdown)

        except Exception as e:
            return ConvertResult(success=False, error_message=f"Conversion failed: {str(e)}")


class _HTMLToMarkdownParser(HTMLParser):
    def __init__(self, heading_map):
        super().__init__()
        self._heading_map = heading_map
        self._result = []
        self._in_pre = False
        self._in_code = False
        self._in_table = False
        self._in_list = False
        self._list_depth = 0
        self._table_rows = []
        self._current_row = []
        self._block_start = False
        self._last_was_newline = False
        self._href = ''

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()

        if tag_lower in self._heading_map:
            self._ensure_newline(2)
            self._result.append(f"{self._heading_map[tag_lower]} ")
            self._block_start = True

        elif tag_lower == 'p':
            self._ensure_newline(2)
            self._block_start = True

        elif tag_lower == 'br':
            self._result.append('\n')
            self._last_was_newline = True

        elif tag_lower == 'hr':
            self._ensure_newline(2)
            self._result.append('---')
            self._ensure_newline(2)
            self._last_was_newline = True

        elif tag_lower == 'strong' or tag_lower == 'b':
            self._result.append('**')

        elif tag_lower == 'em' or tag_lower == 'i':
            self._result.append('*')

        elif tag_lower == 'a':
            href = ''
            for attr_name, attr_value in attrs:
                if attr_name.lower() == 'href':
                    href = attr_value
                    break
            self._result.append('[')
            self._href = href

        elif tag_lower == 'img':
            src = ''
            alt = ''
            for attr_name, attr_value in attrs:
                if attr_name.lower() == 'src':
                    src = attr_value
                elif attr_name.lower() == 'alt':
                    alt = attr_value
            self._result.append(f'![{alt}]({src})')

        elif tag_lower == 'ul':
            self._ensure_newline(2)
            self._in_list = True
            self._list_depth += 1
            self._block_start = True

        elif tag_lower == 'ol':
            self._ensure_newline(2)
            self._in_list = True
            self._list_depth += 1
            self._list_counter = 1
            self._block_start = True

        elif tag_lower == 'li':
            self._ensure_newline()
            if hasattr(self, '_list_counter'):
                self._result.append(f"{self._list_counter}. ")
                self._list_counter += 1
            else:
                self._result.append(f"{'  ' * (self._list_depth - 1)}- ")
            self._block_start = True

        elif tag_lower == 'table':
            self._ensure_newline(2)
            self._in_table = True
            self._table_rows = []

        elif tag_lower == 'tr':
            if self._in_table:
                self._current_row = []

        elif tag_lower == 'td' or tag_lower == 'th':
            if self._in_table:
                self._current_cell = []

        elif tag_lower == 'pre':
            self._ensure_newline(2)
            self._in_pre = True
            self._result.append('```')
            self._ensure_newline()

        elif tag_lower == 'code':
            if not self._in_pre:
                self._result.append('`')
            self._in_code = True

        elif tag_lower == 'blockquote':
            self._ensure_newline(2)
            self._result.append('> ')
            self._block_start = True

    def handle_endtag(self, tag):
        tag_lower = tag.lower()

        if tag_lower in self._heading_map:
            self._ensure_newline(2)

        elif tag_lower == 'p':
            self._ensure_newline(2)

        elif tag_lower == 'strong' or tag_lower == 'b':
            self._result.append('**')

        elif tag_lower == 'em' or tag_lower == 'i':
            self._result.append('*')

        elif tag_lower == 'a':
            self._result.append(f"]({self._href})")

        elif tag_lower == 'ul' or tag_lower == 'ol':
            self._in_list = False
            self._list_depth -= 1
            if self._list_depth == 0:
                self._ensure_newline(2)

        elif tag_lower == 'li':
            self._ensure_newline()

        elif tag_lower == 'table':
            self._ensure_newline(2)
            self._result.append(self._format_table())
            self._ensure_newline(2)
            self._in_table = False

        elif tag_lower == 'tr':
            if self._in_table:
                self._table_rows.append(self._current_row)

        elif tag_lower == 'td' or tag_lower == 'th':
            if self._in_table:
                cell_content = ''.join(self._current_cell).strip()
                self._current_row.append(cell_content)

        elif tag_lower == 'pre':
            self._ensure_newline()
            self._result.append('```')
            self._ensure_newline(2)
            self._in_pre = False

        elif tag_lower == 'code':
            if not self._in_pre:
                self._result.append('`')
            self._in_code = False

        elif tag_lower == 'blockquote':
            self._ensure_newline(2)

        self._block_start = False

    def handle_data(self, data):
        if self._in_pre:
            self._result.append(data)
        elif self._in_table and hasattr(self, '_current_cell'):
            self._current_cell.append(data)
        else:
            if self._block_start and data.strip():
                data = data.lstrip()
                self._block_start = False
            self._result.append(data)

    def handle_entityref(self, name):
        entities = {
            'amp': '&',
            'lt': '<',
            'gt': '>',
            'quot': '"',
            'apos': "'",
        }
        self._result.append(entities.get(name, f'&{name};'))

    def _ensure_newline(self, count=1):
        for _ in range(count):
            if not self._last_was_newline:
                self._result.append('\n')
                self._last_was_newline = True
        if count == 0:
            self._last_was_newline = False

    def _format_table(self):
        if not self._table_rows:
            return ''

        lines = []
        header = self._table_rows[0]
        lines.append('| ' + ' | '.join(header) + ' |')

        separator = '| ' + ' | '.join(['---'] * len(header)) + ' |'
        lines.append(separator)

        for row in self._table_rows[1:]:
            lines.append('| ' + ' | '.join(row) + ' |')

        return '\n'.join(lines)

    def get_result(self):
        result = ''.join(self._result)
        result = '\n'.join(line.rstrip() for line in result.split('\n'))
        return result.strip()
