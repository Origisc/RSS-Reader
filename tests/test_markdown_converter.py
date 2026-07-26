import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.services.markdown_converter import MarkdownConverter, ConvertResult


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


if __name__ == "__main__":
    unittest.main()
