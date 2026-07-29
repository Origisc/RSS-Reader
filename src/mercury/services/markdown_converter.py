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
        self._list_stack = []
        self._table_rows = []
        self._current_row = []
        self._current_cell = None
        self._block_start = False
        self._last_was_newline = False
        self._href_stack = []

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
            self._append_inline('**')

        elif tag_lower == 'em' or tag_lower == 'i':
            self._append_inline('*')

        elif tag_lower == 'a':
            href = ''
            for attr_name, attr_value in attrs:
                if attr_name.lower() == 'href':
                    href = attr_value
                    break
            self._append_inline('[')
            self._href_stack.append(href)

        elif tag_lower == 'img':
            src = ''
            alt = ''
            for attr_name, attr_value in attrs:
                if attr_name.lower() == 'src':
                    src = attr_value
                elif attr_name.lower() == 'alt':
                    alt = attr_value
            self._append_inline(f'![{alt}]({src})')

        elif tag_lower == 'ul':
            self._ensure_newline(2 if not self._list_stack else 1)
            self._list_stack.append({"kind": "ul", "counter": 0})
            self._block_start = True

        elif tag_lower == 'ol':
            start = 1
            for attr_name, attr_value in attrs:
                if attr_name.lower() == "start":
                    try:
                        start = int(attr_value)
                    except (TypeError, ValueError):
                        start = 1
                    break
            self._ensure_newline(2 if not self._list_stack else 1)
            self._list_stack.append({"kind": "ol", "counter": start})
            self._block_start = True

        elif tag_lower == 'li':
            self._ensure_newline()
            depth = max(len(self._list_stack) - 1, 0)
            indent = "    " * depth
            if self._list_stack and self._list_stack[-1]["kind"] == "ol":
                counter = self._list_stack[-1]["counter"]
                self._result.append(f"{indent}{counter}. ")
                self._list_stack[-1]["counter"] = counter + 1
            else:
                self._result.append(f"{indent}- ")
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
                self._append_inline('`')
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
            self._append_inline('**')

        elif tag_lower == 'em' or tag_lower == 'i':
            self._append_inline('*')

        elif tag_lower == 'a':
            href = self._href_stack.pop() if self._href_stack else ""
            self._append_inline(f"]({href})")

        elif tag_lower == 'ul' or tag_lower == 'ol':
            if self._list_stack:
                self._list_stack.pop()
            if not self._list_stack:
                self._ensure_newline(2)
            else:
                self._ensure_newline()

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
            if self._in_table and self._current_cell is not None:
                cell_content = ''.join(self._current_cell).strip()
                self._current_row.append(cell_content)
                self._current_cell = None

        elif tag_lower == 'pre':
            self._ensure_newline()
            self._result.append('```')
            self._ensure_newline(2)
            self._in_pre = False

        elif tag_lower == 'code':
            if not self._in_pre:
                self._append_inline('`')
            self._in_code = False

        elif tag_lower == 'blockquote':
            self._ensure_newline(2)

        self._block_start = False

    def handle_data(self, data):
        if self._in_pre:
            self._result.append(data)
        elif self._in_table and self._current_cell is not None:
            self._current_cell.append(data)
        else:
            if (
                not data.strip()
                and "\n" in data
                and self._last_was_newline
            ):
                return
            if self._block_start and data.strip():
                data = data.lstrip()
                self._block_start = False
            self._result.append(data)
            self._last_was_newline = data.endswith("\n")

    def handle_entityref(self, name):
        entities = {
            'amp': '&',
            'lt': '<',
            'gt': '>',
            'quot': '"',
            'apos': "'",
        }
        self._append_inline(entities.get(name, f'&{name};'))

    def _append_inline(self, value):
        if self._in_table and self._current_cell is not None:
            self._current_cell.append(value)
            return

        self._result.append(value)

    def _ensure_newline(self, count=1):
        if count <= 0:
            self._last_was_newline = False
            return

        trailing_newlines = 0
        for chunk in reversed(self._result):
            chunk_without_newlines = chunk.rstrip("\n")
            trailing_newlines += len(chunk) - len(chunk_without_newlines)
            if chunk_without_newlines:
                break

        missing_newlines = max(count - trailing_newlines, 0)
        if missing_newlines:
            self._result.append("\n" * missing_newlines)
        self._last_was_newline = True

    def _format_table(self):
        if not self._table_rows:
            return ''

        lines = []
        column_count = max(len(row) for row in self._table_rows)
        rows = [
            [self._format_table_cell(cell) for cell in row]
            + [""] * (column_count - len(row))
            for row in self._table_rows
        ]
        header = rows[0]
        lines.append('| ' + ' | '.join(header) + ' |')

        separator = '| ' + ' | '.join(['---'] * column_count) + ' |'
        lines.append(separator)

        for row in rows[1:]:
            lines.append('| ' + ' | '.join(row) + ' |')

        return '\n'.join(lines)

    @staticmethod
    def _format_table_cell(value):
        return value.replace("|", r"\|").replace("\r\n", "<br>").replace(
            "\n",
            "<br>",
        )

    def get_result(self):
        result = ''.join(self._result)
        result = '\n'.join(line.rstrip() for line in result.split('\n'))
        return result.strip()
