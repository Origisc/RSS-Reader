import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.domain import (
    TranslationParagraph,
    TranslationParagraphStatus,
)
from mercury.ui.bilingual_document import interleave_html_translations


def paragraph(
    index: int,
    original: str,
    translated: str,
) -> TranslationParagraph:
    return TranslationParagraph(
        index=index,
        original_text=original,
        translated_text=translated,
        status=TranslationParagraphStatus.TRANSLATED,
        segment_count=1,
        translated_segment_count=1,
    )


class BilingualDocumentTest(unittest.TestCase):
    def test_keeps_original_html_and_inserts_each_translation_in_order(
        self,
    ) -> None:
        source = (
            '<p class="lead">First <strong>bold</strong> '
            '<a href="https://example.com">paragraph</a>.</p>'
            "<blockquote><p>Second paragraph.</p></blockquote>"
            "<ul><li>Third item.</li><li>Fourth item.</li></ul>"
            '<img src="https://example.com/image.png" alt="Diagram">'
        )
        paragraphs = (
            paragraph(0, "First bold paragraph.", "第一段译文。"),
            paragraph(1, "Second paragraph.", "第二段译文。"),
            paragraph(
                2,
                "Third item. Fourth item.",
                "第三、第四项列表译文。",
            ),
        )

        result = interleave_html_translations(
            source,
            paragraphs,
            "译文暂不可用",
        )

        self.assertTrue(result.fully_aligned)
        self.assertEqual(result.inserted_count, 3)
        self.assertIn(
            '<p class="lead">First <strong>bold</strong> '
            '<a href="https://example.com">paragraph</a>.</p>',
            result.html,
        )
        self.assertIn(
            '<img src="https://example.com/image.png" alt="Diagram">',
            result.html,
        )
        first_original = result.html.index("First <strong>bold</strong>")
        first_translation = result.html.index("第一段译文。")
        second_original = result.html.index("Second paragraph.")
        second_translation = result.html.index("第二段译文。")
        third_original = result.html.index("Third item.")
        fourth_original = result.html.index("Fourth item.")
        list_translation = result.html.index("第三、第四项列表译文。")
        self.assertLess(first_original, first_translation)
        self.assertLess(first_translation, second_original)
        self.assertLess(second_original, second_translation)
        self.assertLess(second_translation, third_original)
        self.assertLess(third_original, fourth_original)
        self.assertLess(fourth_original, list_translation)

    def test_alignment_mismatch_is_reported_instead_of_misplacing_text(
        self,
    ) -> None:
        result = interleave_html_translations(
            "<p>Actual original.</p>",
            (paragraph(0, "Different original.", "错误位置的译文。"),),
            "译文暂不可用",
        )

        self.assertFalse(result.fully_aligned)
        self.assertEqual(result.inserted_count, 0)
        self.assertNotIn("错误位置的译文。", result.html)

    def test_image_only_paragraph_does_not_consume_text_translation(
        self,
    ) -> None:
        source = (
            '<p><img src="https://example.com/image.png" '
            'alt="Diagram"></p>'
            "<p>Readable paragraph.</p>"
        )

        result = interleave_html_translations(
            source,
            (paragraph(0, "Readable paragraph.", "可读段落译文。"),),
            "译文暂不可用",
        )

        self.assertTrue(result.fully_aligned)
        self.assertEqual(result.inserted_count, 1)
        self.assertLess(
            result.html.index("Readable paragraph."),
            result.html.index("可读段落译文。"),
        )

    def test_paragraph_indexes_are_sorted_before_html_composition(
        self,
    ) -> None:
        result = interleave_html_translations(
            "<p>First.</p><p>Second.</p>",
            (
                paragraph(1, "Second.", "第二段。"),
                paragraph(0, "First.", "第一段。"),
            ),
            "译文暂不可用",
        )

        self.assertTrue(result.fully_aligned)
        self.assertLess(
            result.html.index("First."),
            result.html.index("第一段。"),
        )
        self.assertLess(
            result.html.index("第一段。"),
            result.html.index("Second."),
        )
        self.assertLess(
            result.html.index("Second."),
            result.html.index("第二段。"),
        )


if __name__ == "__main__":
    unittest.main()
