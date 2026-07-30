import re
from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
from typing import Optional


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


_HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)')
_ORDERED_LIST_RE = re.compile(r'^(\s*)(\d+)\.\s+(.*)')
_UNORDERED_LIST_RE = re.compile(r'^(\s*)[-*+]\s+(.*)')
_BLOCKQUOTE_RE = re.compile(r'^>\s?(.*)')
_CODE_FENCE_RE = re.compile(r'^```')
_TABLE_ROW_RE = re.compile(r'^\|.*\|$')
_TABLE_SEPARATOR_RE = re.compile(r'^\|[\s:-]+\|$')
_HORIZONTAL_RULE_RE = re.compile(r'^\s*---\s*$')
_LINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
_IMAGE_RE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
_BOLD_RE = re.compile(r'\*\*(.+?)\*\*')
_ITALIC_RE = re.compile(r'(?<!\*)\*(?!\s)(.+?)(?<!\s)\*')
_CODE_SPAN_RE = re.compile(r'`([^`]+)`')


class MarkdownRenderer:
    """Render a limited Markdown subset to HTML for display in QTextBrowser.

    Supports the exact subset produced by :class:`MarkdownConverter`:
    headings, paragraphs, bold/italic/code spans, links, images,
    ordered/unordered lists (with nesting), code fences, blockquotes,
    GFM tables, and horizontal rules.
    """

    def render(self, markdown: str) -> str:
        if not markdown or not markdown.strip():
            return ""

        lines = markdown.split('\n')
        blocks = self._parse_blocks(lines)
        html_parts: list[str] = []
        for block in blocks:
            html_parts.append(self._render_block(block))
        return '\n'.join(html_parts)

    def _parse_blocks(self, lines: list[str]) -> list[dict]:
        blocks: list[dict] = []
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]

            if _HORIZONTAL_RULE_RE.match(line):
                blocks.append({'type': 'hr'})
                i += 1
                continue

            heading_match = _HEADING_RE.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
                blocks.append({'type': 'heading', 'level': level, 'text': text})
                i += 1
                continue

            if _CODE_FENCE_RE.match(line):
                lang = line.strip()[3:].strip()
                code_lines: list[str] = []
                i += 1
                while i < n and not _CODE_FENCE_RE.match(lines[i]):
                    code_lines.append(lines[i])
                    i += 1
                if i < n:
                    i += 1
                blocks.append({
                    'type': 'code_block',
                    'lang': lang,
                    'code': '\n'.join(code_lines),
                })
                continue

            if _TABLE_ROW_RE.match(line):
                table_lines: list[str] = [line]
                i += 1
                while i < n and _TABLE_ROW_RE.match(lines[i]):
                    table_lines.append(lines[i])
                    i += 1
                blocks.append(self._parse_table(table_lines))
                continue

            list_blocks, consumed = self._try_parse_list(lines, i)
            if list_blocks:
                blocks.extend(list_blocks)
                i += consumed
                continue

            quote_lines: list[str] = []
            while i < n:
                m = _BLOCKQUOTE_RE.match(lines[i])
                if m:
                    quote_lines.append(m.group(1))
                    i += 1
                else:
                    break
            if quote_lines:
                quote_text = ' '.join(l.strip() for l in quote_lines)
                blocks.append({'type': 'blockquote', 'text': quote_text})
                continue

            if line.strip() == '':
                i += 1
                continue

            para_lines: list[str] = []
            while i < n and lines[i].strip() != '':
                if self._is_block_start(lines[i]):
                    break
                para_lines.append(lines[i])
                i += 1
            if para_lines:
                text = ' '.join(l.strip() for l in para_lines)
                blocks.append({'type': 'paragraph', 'text': text})
                continue

            i += 1

        return blocks

    @staticmethod
    def _is_block_start(line: str) -> bool:
        if not line.strip():
            return False
        return bool(
            _HEADING_RE.match(line)
            or _ORDERED_LIST_RE.match(line)
            or _UNORDERED_LIST_RE.match(line)
            or _CODE_FENCE_RE.match(line)
            or _TABLE_ROW_RE.match(line)
            or _BLOCKQUOTE_RE.match(line)
            or _HORIZONTAL_RULE_RE.match(line)
        )

    def _try_parse_list(
        self,
        lines: list[str],
        start: int,
    ) -> tuple[list[dict], int]:
        if start >= len(lines):
            return [], 0

        first = lines[start]
        ordered_match = _ORDERED_LIST_RE.match(first)
        unordered_match = _UNORDERED_LIST_RE.match(first)

        if not ordered_match and not unordered_match:
            return [], 0

        raw_items: list[dict] = []
        i = start

        while i < len(lines):
            line = lines[i]
            if line.strip() == '':
                break

            om = _ORDERED_LIST_RE.match(line)
            um = _UNORDERED_LIST_RE.match(line)

            if not om and not um:
                break

            if om:
                indent = len(om.group(1))
                number = int(om.group(2))
                text = om.group(3).strip()
                raw_items.append({
                    'kind': 'ol',
                    'indent': indent,
                    'text': text,
                    'number': number,
                })
            else:
                indent = len(um.group(1))
                text = um.group(2).strip()
                raw_items.append({
                    'kind': 'ul',
                    'indent': indent,
                    'text': text,
                    'number': 0,
                })
            i += 1

        if not raw_items:
            return [], 0

        list_root = self._build_list_tree(raw_items)
        return [list_root], i - start

    def _build_list_tree(self, items: list[dict]) -> dict:
        if not items:
            return {'type': 'list', 'kind': 'ul', 'items': []}

        min_indent = min(it['indent'] for it in items)
        kind = items[0]['kind']

        root_items: list[dict] = []
        i = 0
        n = len(items)

        while i < n:
            item = items[i]
            if item['indent'] == min_indent:
                sub_items: list[dict] = []
                j = i + 1
                while j < n and items[j]['indent'] > min_indent:
                    sub_items.append(items[j])
                    j += 1

                child_list = None
                if sub_items:
                    child_list = self._build_list_tree(sub_items)

                root_items.append({
                    'text': item['text'],
                    'number': item['number'],
                    'child': child_list,
                })
                i = j
            else:
                i += 1

        return {
            'type': 'list',
            'kind': kind,
            'items': root_items,
        }

    @staticmethod
    def _parse_table(table_lines: list[str]) -> dict:
        rows: list[list[str]] = []
        for line in table_lines:
            cells = [c.strip() for c in line.strip('|').split('|')]
            rows.append(cells)

        if len(rows) >= 2:
            header = rows[0]
            data_rows = rows[2:]
        elif len(rows) == 1:
            header = rows[0]
            data_rows = []
        else:
            header = []
            data_rows = []

        return {
            'type': 'table',
            'header': header,
            'rows': data_rows,
        }

    def _render_block(self, block: dict) -> str:
        block_type = block['type']

        if block_type == 'heading':
            level = block['level']
            text = self._render_inline(block['text'])
            return f'<h{level}>{text}</h{level}>'

        if block_type == 'paragraph':
            text = self._render_inline(block['text'])
            return f'<p>{text}</p>'

        if block_type == 'code_block':
            lang = block.get('lang', '')
            code = block['code']
            lang_attr = f' class="language-{lang}"' if lang else ''
            return f'<pre><code{lang_attr}>{escape(code)}</code></pre>'

        if block_type == 'blockquote':
            text = self._render_inline(block['text'])
            return f'<blockquote>{text}</blockquote>'

        if block_type == 'hr':
            return '<hr/>'

        if block_type == 'table':
            return self._render_table(block)

        if block_type == 'list':
            return self._render_list(block)

        return ''

    def _render_list(self, list_block: dict) -> str:
        kind = list_block['kind']
        items = list_block['items']
        tag = 'ol' if kind == 'ol' else 'ul'

        parts: list[str] = [f'<{tag}>']
        for item in items:
            text_html = self._render_inline(item['text'])
            child_html = ''
            if item.get('child'):
                child_html = self._render_list(item['child'])
            parts.append(f'<li>{text_html}{child_html}</li>')
        parts.append(f'</{tag}>')
        return ''.join(parts)

    def _render_table(self, table: dict) -> str:
        header = table['header']
        rows = table['rows']
        parts: list[str] = ['<table>']

        if header:
            parts.append('<thead><tr>')
            for cell in header:
                cell_html = self._render_inline(cell)
                parts.append(f'<th>{cell_html}</th>')
            parts.append('</tr></thead>')

        if rows:
            parts.append('<tbody>')
            for row in rows:
                parts.append('<tr>')
                for cell in row:
                    cell_html = self._render_inline(cell)
                    parts.append(f'<td>{cell_html}</td>')
                parts.append('</tr>')
            parts.append('</tbody>')

        parts.append('</table>')
        return ''.join(parts)

    def _render_inline(self, text: str) -> str:
        result = text

        result = self._process_code_spans(result)
        result = self._process_images(result)
        result = self._process_links(result)
        result = self._process_bold(result)
        result = self._process_italic(result)

        return result

    def _process_code_spans(self, text: str) -> str:
        result_parts: list[str] = []
        last_end = 0
        for match in _CODE_SPAN_RE.finditer(text):
            result_parts.append(text[last_end:match.start()])
            code_content = escape(match.group(1))
            result_parts.append(f'<code>{code_content}</code>')
            last_end = match.end()
        result_parts.append(text[last_end:])
        return ''.join(result_parts)

    def _process_images(self, text: str) -> str:
        def replacer(m: re.Match[str]) -> str:
            alt = escape(m.group(1))
            src = escape(m.group(2), quote=True)
            return f'<img src="{src}" alt="{alt}"/>'

        return _IMAGE_RE.sub(replacer, text)

    def _process_links(self, text: str) -> str:
        def replacer(m: re.Match[str]) -> str:
            inner_text = self._render_inline(m.group(1))
            href = escape(m.group(2), quote=True)
            return f'<a href="{href}">{inner_text}</a>'

        return _LINK_RE.sub(replacer, text)

    def _process_bold(self, text: str) -> str:
        def replacer(m: re.Match[str]) -> str:
            inner = self._render_inline(m.group(1))
            return f'<strong>{inner}</strong>'

        return _BOLD_RE.sub(replacer, text)

    def _process_italic(self, text: str) -> str:
        def replacer(m: re.Match[str]) -> str:
            inner = self._render_inline(m.group(1))
            return f'<em>{inner}</em>'

        return _ITALIC_RE.sub(replacer, text)
