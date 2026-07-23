import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.services.reader_cleaner import ReaderCleaner, CleanResult


class ReaderCleanerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cleaner = ReaderCleaner()

    def test_clean_empty_html(self) -> None:
        result = self.cleaner.clean("")
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "HTML content is empty")

    def test_clean_none_html(self) -> None:
        result = self.cleaner.clean(None)
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "HTML content is empty")

    def test_clean_removes_scripts(self) -> None:
        html = """<html>
<head><script>alert('test');</script></head>
<body><p>Content</p></body>
</html>"""
        result = self.cleaner.clean(html)
        self.assertTrue(result.success)
        self.assertNotIn("<script>", result.cleaned_html)
        self.assertNotIn("alert", result.cleaned_html)

    def test_clean_removes_styles(self) -> None:
        html = """<html>
<head><style>body { color: red; }</style></head>
<body><p>Content</p></body>
</html>"""
        result = self.cleaner.clean(html)
        self.assertTrue(result.success)
        self.assertNotIn("<style>", result.cleaned_html)
        self.assertNotIn("color: red", result.cleaned_html)

    def test_clean_removes_comments(self) -> None:
        html = """<html>
<body>
<!-- This is a comment -->
<p>Content</p>
</body>
</html>"""
        result = self.cleaner.clean(html)
        self.assertTrue(result.success)
        self.assertNotIn("<!--", result.cleaned_html)
        self.assertNotIn("comment", result.cleaned_html)

    def test_clean_preserves_headings(self) -> None:
        html = """<html>
<body>
<h1>Heading 1</h1>
<h2>Heading 2</h2>
<h3>Heading 3</h3>
<p>Content</p>
</body>
</html>"""
        result = self.cleaner.clean(html)
        self.assertTrue(result.success)
        self.assertIn("<h1>", result.cleaned_html)
        self.assertIn("Heading 1", result.cleaned_html)
        self.assertIn("</h1>", result.cleaned_html)
        self.assertIn("<h2>", result.cleaned_html)
        self.assertIn("Heading 2", result.cleaned_html)
        self.assertIn("</h2>", result.cleaned_html)
        self.assertIn("<h3>", result.cleaned_html)
        self.assertIn("Heading 3", result.cleaned_html)
        self.assertIn("</h3>", result.cleaned_html)

    def test_clean_preserves_paragraphs(self) -> None:
        html = """<html>
<body>
<p>First paragraph</p>
<p>Second paragraph</p>
</body>
</html>"""
        result = self.cleaner.clean(html)
        self.assertTrue(result.success)
        self.assertIn("<p>", result.cleaned_html)
        self.assertIn("First paragraph", result.cleaned_html)
        self.assertIn("Second paragraph", result.cleaned_html)

    def test_clean_preserves_links(self) -> None:
        html = """<html>
<body>
<p>Visit <a href="https://example.com">Example</a></p>
</body>
</html>"""
        result = self.cleaner.clean(html)
        self.assertTrue(result.success)
        self.assertIn('<a href="https://example.com">Example</a>', result.cleaned_html)

    def test_clean_preserves_images(self) -> None:
        html = """<html>
<body>
<img src="https://example.com/image.jpg" alt="Test Image">
</body>
</html>"""
        result = self.cleaner.clean(html)
        self.assertTrue(result.success)
        self.assertIn('<img src="https://example.com/image.jpg" alt="Test Image">', result.cleaned_html)

    def test_clean_preserves_lists(self) -> None:
        html = """<html>
<body>
<ul>
<li>Item 1</li>
<li>Item 2</li>
</ul>
<ol>
<li>Ordered 1</li>
<li>Ordered 2</li>
</ol>
</body>
</html>"""
        result = self.cleaner.clean(html)
        self.assertTrue(result.success)
        self.assertIn("<ul>", result.cleaned_html)
        self.assertIn("<ol>", result.cleaned_html)
        self.assertIn("<li>Item 1</li>", result.cleaned_html)

    def test_clean_preserves_tables(self) -> None:
        html = """<html>
<body>
<table>
<tr><th>Column 1</th><th>Column 2</th></tr>
<tr><td>Data 1</td><td>Data 2</td></tr>
</table>
</body>
</html>"""
        result = self.cleaner.clean(html)
        self.assertTrue(result.success)
        self.assertIn("<table>", result.cleaned_html)
        self.assertIn("<tr>", result.cleaned_html)
        self.assertIn("<th>", result.cleaned_html)
        self.assertIn("<td>", result.cleaned_html)

    def test_clean_preserves_code_blocks(self) -> None:
        html = """<html>
<body>
<pre><code>def hello():
    print("Hello")</code></pre>
</body>
</html>"""
        result = self.cleaner.clean(html)
        self.assertTrue(result.success)
        self.assertIn("<pre>", result.cleaned_html)
        self.assertIn("<code>", result.cleaned_html)
        self.assertIn("def hello():", result.cleaned_html)

    def test_clean_preserves_blockquotes(self) -> None:
        html = """<html>
<body>
<blockquote>This is a quote</blockquote>
</body>
</html>"""
        result = self.cleaner.clean(html)
        self.assertTrue(result.success)
        self.assertIn("<blockquote>", result.cleaned_html)
        self.assertIn("This is a quote", result.cleaned_html)
        self.assertIn("</blockquote>", result.cleaned_html)

    def test_clean_removes_attributes(self) -> None:
        html = """<html>
<body>
<p class="test" id="para" style="color:red; font-size:12px">Content</p>
</body>
</html>"""
        result = self.cleaner.clean(html)
        self.assertTrue(result.success)
        self.assertNotIn('class="test"', result.cleaned_html)
        self.assertNotIn('id="para"', result.cleaned_html)
        self.assertNotIn('style="', result.cleaned_html)

    def test_clean_extracts_article_tag(self) -> None:
        html = """<html>
<body>
<header>Navigation</header>
<article>
<h1>Article Title</h1>
<p>Article content</p>
</article>
<footer>Footer</footer>
</body>
</html>"""
        result = self.cleaner.clean(html)
        self.assertTrue(result.success)
        self.assertIn("Article Title", result.cleaned_html)
        self.assertIn("Article content", result.cleaned_html)

    def test_clean_result_dataclass(self) -> None:
        result = CleanResult(success=True, cleaned_html="<p>content</p>")
        self.assertTrue(result.success)
        self.assertEqual(result.cleaned_html, "<p>content</p>")
        self.assertIsNone(result.error_message)

        result_fail = CleanResult(success=False, error_message="cleaning failed")
        self.assertFalse(result_fail.success)
        self.assertEqual(result_fail.error_message, "cleaning failed")


if __name__ == "__main__":
    unittest.main()
