import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.services.markdown_converter import (
    MarkdownConverter,
    MarkdownRenderer,
    ConvertResult,
)


class MarkdownConverterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.converter = MarkdownConverter()

    def test_convert_empty_html(self) -> None:
        result = self.converter.convert("")
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "HTML content is empty")

    def test_convert_none_html(self) -> None:
        result = self.converter.convert(None)
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "HTML content is empty")

    def test_convert_headings(self) -> None:
        html = """<h1>Heading 1</h1>
<h2>Heading 2</h2>
<h3>Heading 3</h3>"""
        result = self.converter.convert(html)
        self.assertTrue(result.success)
        self.assertIn("# Heading 1", result.markdown)
        self.assertIn("## Heading 2", result.markdown)
        self.assertIn("### Heading 3", result.markdown)

    def test_convert_paragraphs(self) -> None:
        html = """<p>First paragraph</p>
<p>Second paragraph</p>"""
        result = self.converter.convert(html)
        self.assertTrue(result.success)
        self.assertIn("First paragraph", result.markdown)
        self.assertIn("Second paragraph", result.markdown)
        self.assertEqual(
            result.markdown,
            "First paragraph\n\nSecond paragraph",
        )

    def test_convert_links(self) -> None:
        html = '<p>Visit <a href="https://example.com">Example</a></p>'
        result = self.converter.convert(html)
        self.assertTrue(result.success)
        self.assertIn("[Example](https://example.com)", result.markdown)

    def test_convert_images(self) -> None:
        html = '<img src="https://example.com/image.jpg" alt="Test Image">'
        result = self.converter.convert(html)
        self.assertTrue(result.success)
        self.assertIn("![Test Image](https://example.com/image.jpg)", result.markdown)

    def test_convert_unordered_lists(self) -> None:
        html = """<ul>
<li>Item 1</li>
<li>Item 2</li>
</ul>"""
        result = self.converter.convert(html)
        self.assertTrue(result.success)
        self.assertIn("- Item 1", result.markdown)
        self.assertIn("- Item 2", result.markdown)

    def test_convert_ordered_lists(self) -> None:
        html = """<ol>
<li>First</li>
<li>Second</li>
</ol>"""
        result = self.converter.convert(html)
        self.assertTrue(result.success)
        self.assertIn("1. First", result.markdown)
        self.assertIn("2. Second", result.markdown)

    def test_convert_nested_mixed_lists_preserves_markers_and_depth(
        self,
    ) -> None:
        html = """<ol>
<li>First
<ul>
<li>Nested bullet</li>
</ul>
</li>
<li>Second
<ol start="4">
<li>Nested numbered</li>
</ol>
</li>
</ol>"""

        result = self.converter.convert(html)

        self.assertTrue(result.success)
        self.assertIn("1. First", result.markdown)
        self.assertIn("    - Nested bullet", result.markdown)
        self.assertIn("2. Second", result.markdown)
        self.assertIn("    4. Nested numbered", result.markdown)

    def test_convert_tables(self) -> None:
        html = """<table>
<tr><th>Name</th><th>Age</th></tr>
<tr><td>John</td><td>30</td></tr>
<tr><td>Jane</td><td>25</td></tr>
</table>"""
        result = self.converter.convert(html)
        self.assertTrue(result.success)
        self.assertIn("| Name | Age |", result.markdown)
        self.assertIn("| --- | --- |", result.markdown)
        self.assertIn("| John | 30 |", result.markdown)
        self.assertIn("| Jane | 25 |", result.markdown)

    def test_convert_table_cells_preserves_inline_markdown(self) -> None:
        html = """<table>
<tr><th>Kind</th><th>Value</th></tr>
<tr><td><strong>Bold</strong></td><td><em>Italic</em></td></tr>
<tr><td><code>inline()</code></td><td><a href="https://example.com">Link</a></td></tr>
</table>"""

        result = self.converter.convert(html)

        self.assertTrue(result.success)
        self.assertIn("| **Bold** | *Italic* |", result.markdown)
        self.assertIn(
            "| `inline()` | [Link](https://example.com) |",
            result.markdown,
        )

    def test_convert_code_blocks(self) -> None:
        html = """<pre><code>def hello():
    print("Hello World")</code></pre>"""
        result = self.converter.convert(html)
        self.assertTrue(result.success)
        self.assertIn("```", result.markdown)
        self.assertIn("def hello():", result.markdown)
        self.assertIn('print("Hello World")', result.markdown)

    def test_convert_inline_code(self) -> None:
        html = '<p>Use <code>python</code> for scripting</p>'
        result = self.converter.convert(html)
        self.assertTrue(result.success)
        self.assertIn("`python`", result.markdown)

    def test_convert_blockquotes(self) -> None:
        html = "<blockquote>This is a quote</blockquote>"
        result = self.converter.convert(html)
        self.assertTrue(result.success)
        self.assertIn("> This is a quote", result.markdown)

    def test_convert_bold_and_italic(self) -> None:
        html = '<p><strong>Bold</strong> and <em>italic</em> text</p>'
        result = self.converter.convert(html)
        self.assertTrue(result.success)
        self.assertIn("**Bold**", result.markdown)
        self.assertIn("*italic*", result.markdown)

    def test_convert_horizontal_rule(self) -> None:
        html = "<hr>"
        result = self.converter.convert(html)
        self.assertTrue(result.success)
        self.assertIn("---", result.markdown)

    def test_convert_line_break(self) -> None:
        html = "<p>Line 1<br>Line 2</p>"
        result = self.converter.convert(html)
        self.assertTrue(result.success)
        self.assertIn("Line 1", result.markdown)
        self.assertIn("Line 2", result.markdown)

    def test_convert_complex_content(self) -> None:
        html = """<html>
<body>
<h1>Sample Article</h1>
<p>This is a paragraph with <a href="https://example.com">a link</a>.</p>
<ul>
<li>List item 1</li>
<li>List item 2</li>
</ul>
<blockquote>Blockquote text</blockquote>
<pre><code>code snippet</code></pre>
</body>
</html>"""
        result = self.converter.convert(html)
        self.assertTrue(result.success)
        self.assertIn("# Sample Article", result.markdown)
        self.assertIn("[a link](https://example.com)", result.markdown)
        self.assertIn("- List item 1", result.markdown)
        self.assertIn("> Blockquote text", result.markdown)
        self.assertIn("code snippet", result.markdown)

    def test_convert_result_dataclass(self) -> None:
        result = ConvertResult(success=True, markdown="# Title")
        self.assertTrue(result.success)
        self.assertEqual(result.markdown, "# Title")
        self.assertIsNone(result.error_message)

        result_fail = ConvertResult(success=False, error_message="conversion failed")
        self.assertFalse(result_fail.success)
        self.assertEqual(result_fail.error_message, "conversion failed")


class MarkdownRendererTest(unittest.TestCase):
    def setUp(self) -> None:
        self.renderer = MarkdownRenderer()

    def test_render_empty_returns_empty_string(self) -> None:
        self.assertEqual(self.renderer.render(""), "")
        self.assertEqual(self.renderer.render("   "), "")

    def test_render_headings(self) -> None:
        md = "# H1\n\n## H2\n\n### H3"
        html = self.renderer.render(md)
        self.assertIn("<h1>H1</h1>", html)
        self.assertIn("<h2>H2</h2>", html)
        self.assertIn("<h3>H3</h3>", html)

    def test_render_paragraphs(self) -> None:
        md = "First paragraph.\n\nSecond paragraph."
        html = self.renderer.render(md)
        self.assertIn("<p>First paragraph.</p>", html)
        self.assertIn("<p>Second paragraph.</p>", html)

    def test_render_long_url_link_is_not_broken_character_by_character(
        self,
    ) -> None:
        long_url = (
            "https://www.lukesavage.com/p/"
            "the-enshittification-of-life-the-universe-and-everything"
        )
        md = f"[Luke Savage]({long_url})"
        html = self.renderer.render(md)
        self.assertIn(f'href="{long_url}"', html)
        self.assertIn(">Luke Savage<", html)
        self.assertNotIn("href=\"h\"", html)

    def test_render_unordered_list(self) -> None:
        md = "- Item 1\n- Item 2"
        html = self.renderer.render(md)
        self.assertIn("<ul>", html)
        self.assertIn("<li>Item 1</li>", html)
        self.assertIn("<li>Item 2</li>", html)
        self.assertIn("</ul>", html)

    def test_render_ordered_list(self) -> None:
        md = "1. First\n2. Second"
        html = self.renderer.render(md)
        self.assertIn("<ol>", html)
        self.assertIn("<li>First</li>", html)
        self.assertIn("<li>Second</li>", html)
        self.assertIn("</ol>", html)

    def test_render_nested_list(self) -> None:
        md = "- Top\n    - Nested\n        - Deep"
        html = self.renderer.render(md)
        self.assertIn("<ul>", html)
        self.assertIn("</ul>", html)
        self.assertIn("<li>Top", html)
        self.assertIn("<li>Nested", html)
        self.assertIn("<li>Deep", html)

    def test_render_inline_bold(self) -> None:
        md = "**bold text**"
        html = self.renderer.render(md)
        self.assertIn("<strong>bold text</strong>", html)

    def test_render_inline_italic(self) -> None:
        md = "*italic text*"
        html = self.renderer.render(md)
        self.assertIn("<em>italic text</em>", html)

    def test_render_inline_code(self) -> None:
        md = "Use `python` here"
        html = self.renderer.render(md)
        self.assertIn("<code>python</code>", html)

    def test_render_link(self) -> None:
        md = "[Click here](https://example.com)"
        html = self.renderer.render(md)
        self.assertIn('<a href="https://example.com">Click here</a>', html)

    def test_render_image(self) -> None:
        md = "![Alt text](https://example.com/img.png)"
        html = self.renderer.render(md)
        self.assertIn(
            '<img src="https://example.com/img.png" alt="Alt text"/>',
            html,
        )

    def test_render_code_block(self) -> None:
        md = "```python\nprint('hello')\n```"
        html = self.renderer.render(md)
        self.assertIn("<pre><code", html)
        self.assertIn("print(&#x27;hello&#x27;)", html)
        self.assertIn("</code></pre>", html)

    def test_render_blockquote(self) -> None:
        md = "> This is a quote"
        html = self.renderer.render(md)
        self.assertIn("<blockquote>This is a quote</blockquote>", html)

    def test_render_table(self) -> None:
        md = "| Name | Age |\n| --- | --- |\n| John | 30 |"
        html = self.renderer.render(md)
        self.assertIn("<table>", html)
        self.assertIn("<th>Name</th>", html)
        self.assertIn("<th>Age</th>", html)
        self.assertIn("<td>John</td>", html)
        self.assertIn("<td>30</td>", html)
        self.assertIn("</table>", html)

    def test_render_horizontal_rule(self) -> None:
        md = "---"
        html = self.renderer.render(md)
        self.assertIn("<hr/>", html)

    def test_render_mixed_inline_formatting(self) -> None:
        md = "**Bold** and *italic* and `code` and [link](https://example.com)"
        html = self.renderer.render(md)
        self.assertIn("<strong>Bold</strong>", html)
        self.assertIn("<em>italic</em>", html)
        self.assertIn("<code>code</code>", html)
        self.assertIn('<a href="https://example.com">link</a>', html)

    def test_render_link_with_inline_formatting(self) -> None:
        md = "[**bold link**](https://example.com)"
        html = self.renderer.render(md)
        self.assertIn('<a href="https://example.com">', html)
        self.assertIn("<strong>bold link</strong>", html)

    def test_render_produces_valid_html_structure(self) -> None:
        md = "# Title\n\nParagraph text.\n\n- List item"
        html = self.renderer.render(md)
        self.assertTrue(html.startswith("<h1>"))
        self.assertIn("<p>", html)
        self.assertIn("<ul>", html)
        self.assertIn("<li>", html)


if __name__ == "__main__":
    unittest.main()
