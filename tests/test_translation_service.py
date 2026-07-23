import sys
import unittest
from unittest.mock import MagicMock
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.llm.provider import LLMResult
from mercury.services.translation_service import TranslationService, ParagraphPair


class MockFailingProvider:
    def __init__(self, fail_on_paragraph: int = -1):
        self._fail_on_paragraph = fail_on_paragraph
        self._call_count = 0

    def chat(self, messages, **kwargs):
        self._call_count += 1
        if self._fail_on_paragraph > 0 and self._call_count == self._fail_on_paragraph:
            return LLMResult(success=False, error_message="API error")
        return LLMResult(success=True, content="Translated paragraph")

    def get_name(self):
        return "MockFailingProvider"


class TestTranslationService(unittest.TestCase):
    def test_translate_empty_text(self):
        provider = MagicMock()
        service = TranslationService(provider)

        result = service.translate("")
        self.assertFalse(result.success)
        self.assertIn("empty", result.error_message.lower())

        result = service.translate("   ")
        self.assertFalse(result.success)
        self.assertIn("empty", result.error_message.lower())

    def test_translate_single_paragraph(self):
        provider = MagicMock()
        provider.chat.return_value = LLMResult(success=True, content="这是翻译后的文本")
        service = TranslationService(provider)

        result = service.translate("This is a test paragraph.")

        self.assertTrue(result.success)
        self.assertEqual(result.translated_text, "这是翻译后的文本")
        self.assertEqual(result.paragraph_count, 1)
        self.assertEqual(result.failed_paragraphs, 0)

    def test_translate_multiple_paragraphs(self):
        provider = MagicMock()
        provider.chat.return_value = LLMResult(success=True, content="翻译段落")
        service = TranslationService(provider)

        text = """First paragraph.

Second paragraph.

Third paragraph."""

        result = service.translate(text)

        self.assertTrue(result.success)
        self.assertEqual(result.paragraph_count, 3)
        self.assertEqual(result.failed_paragraphs, 0)
        self.assertEqual(provider.chat.call_count, 3)

    def test_translate_with_empty_lines(self):
        provider = MagicMock()
        provider.chat.return_value = LLMResult(success=True, content="翻译")
        service = TranslationService(provider)

        text = """Paragraph 1


Paragraph 2

"""

        result = service.translate(text)

        self.assertTrue(result.success)
        self.assertEqual(result.paragraph_count, 2)

    def test_translate_single_paragraph_failure(self):
        provider = MockFailingProvider(fail_on_paragraph=1)
        service = TranslationService(provider)

        result = service.translate("This is a test paragraph.")

        self.assertFalse(result.success)
        self.assertEqual(result.paragraph_count, 1)
        self.assertEqual(result.failed_paragraphs, 1)

    def test_translate_some_paragraphs_failure(self):
        provider = MockFailingProvider(fail_on_paragraph=2)
        service = TranslationService(provider)

        text = """First paragraph.

Second paragraph.

Third paragraph."""

        result = service.translate(text)

        self.assertTrue(result.success)
        self.assertEqual(result.paragraph_count, 3)
        self.assertEqual(result.failed_paragraphs, 1)

    def test_translate_all_paragraphs_failure(self):
        provider = MagicMock()
        provider.chat.return_value = LLMResult(success=False, error_message="All failed")
        service = TranslationService(provider)

        text = """First paragraph.

Second paragraph."""

        result = service.translate(text)

        self.assertFalse(result.success)
        self.assertEqual(result.paragraph_count, 2)
        self.assertEqual(result.failed_paragraphs, 2)

    def test_split_into_paragraphs(self):
        provider = MagicMock()
        service = TranslationService(provider)

        text = """Line 1
Line 2

Line 3

Line 4
Line 5"""

        paragraphs = service._split_into_paragraphs(text)

        self.assertEqual(len(paragraphs), 3)
        self.assertEqual(paragraphs[0], "Line 1 Line 2")
        self.assertEqual(paragraphs[1], "Line 3")
        self.assertEqual(paragraphs[2], "Line 4 Line 5")

    def test_split_into_paragraphs_empty(self):
        provider = MagicMock()
        service = TranslationService(provider)

        paragraphs = service._split_into_paragraphs("")
        self.assertEqual(len(paragraphs), 0)

        paragraphs = service._split_into_paragraphs("   ")
        self.assertEqual(len(paragraphs), 0)

    def test_translate_with_对照(self):
        provider = MagicMock()
        provider.chat.return_value = LLMResult(success=True, content="翻译段落")
        service = TranslationService(provider)

        text = """First paragraph.

Second paragraph."""

        translated_text, pairs = service.translate_with对照(text)

        self.assertTrue(translated_text)
        self.assertEqual(len(pairs), 2)
        self.assertTrue(pairs[0].success)
        self.assertTrue(pairs[1].success)

    def test_translate_with_对照_partial_failure(self):
        provider = MockFailingProvider(fail_on_paragraph=2)
        service = TranslationService(provider)

        text = """First paragraph.

Second paragraph."""

        translated_text, pairs = service.translate_with对照(text)

        self.assertTrue(pairs[0].success)
        self.assertFalse(pairs[1].success)
        self.assertEqual(pairs[1].translated, "Second paragraph.")

    def test_get_provider_name(self):
        provider = MagicMock()
        provider.get_name.return_value = "TestProvider"
        service = TranslationService(provider)

        self.assertEqual(service.get_provider_name(), "TestProvider")

    def test_translate_different_language(self):
        provider = MagicMock()
        provider.chat.return_value = LLMResult(success=True, content="Japanese translation")
        service = TranslationService(provider)

        result = service.translate("English text", target_language="ja")

        self.assertTrue(result.success)
        messages = provider.chat.call_args[0][0]
        self.assertIn("ja", messages[1]["content"])


if __name__ == "__main__":
    unittest.main()