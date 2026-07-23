from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Tuple
import re

from mercury.llm.provider import LLMProvider, LLMResult


@dataclass
class TranslationResult:
    success: bool
    translated_text: str = ""
    error_message: Optional[str] = None
    paragraph_count: int = 0
    failed_paragraphs: int = 0


@dataclass
class ParagraphPair:
    original: str
    translated: str
    success: bool
    error: Optional[str] = None


class TranslationService:
    def __init__(self, provider: LLMProvider):
        self._provider = provider

    def translate(self, text: str, target_language: str = "zh") -> TranslationResult:
        if not text or not text.strip():
            return TranslationResult(success=False, error_message="Text content is empty")

        paragraphs = self._split_into_paragraphs(text)
        if not paragraphs:
            return TranslationResult(success=False, error_message="No paragraphs to translate")

        pairs = self._translate_paragraphs(paragraphs, target_language)
        translated_text = self._merge_pairs(pairs)

        failed_count = sum(1 for p in pairs if not p.success)
        success = failed_count == 0 or failed_count < len(pairs)

        if success and not translated_text.strip():
            return TranslationResult(success=False, error_message="Translated content is empty")

        return TranslationResult(
            success=success,
            translated_text=translated_text,
            paragraph_count=len(paragraphs),
            failed_paragraphs=failed_count,
        )

    def _split_into_paragraphs(self, text: str) -> List[str]:
        lines = text.split("\n")
        paragraphs = []
        current_paragraph = []

        for line in lines:
            stripped = line.strip()
            if stripped:
                current_paragraph.append(stripped)
            elif current_paragraph:
                paragraphs.append(" ".join(current_paragraph))
                current_paragraph = []

        if current_paragraph:
            paragraphs.append(" ".join(current_paragraph))

        return paragraphs

    def _translate_paragraphs(self, paragraphs: List[str], target_language: str) -> List[ParagraphPair]:
        pairs = []
        for idx, paragraph in enumerate(paragraphs, 1):
            if not paragraph.strip():
                pairs.append(ParagraphPair(original=paragraph, translated="", success=True))
                continue

            result = self._translate_single_paragraph(paragraph, target_language)
            if result.success:
                pairs.append(ParagraphPair(
                    original=paragraph,
                    translated=result.content.strip(),
                    success=True,
                ))
            else:
                pairs.append(ParagraphPair(
                    original=paragraph,
                    translated=paragraph,
                    success=False,
                    error=result.error_message,
                ))

        return pairs

    def _translate_single_paragraph(self, paragraph: str, target_language: str) -> LLMResult:
        prompt = (
            f"Translate the following text to {target_language}. "
            "Keep the original meaning and tone. "
            "Do not add any extra explanation or content. "
            "Only return the translated text.\n\n"
            f"Text: {paragraph}"
        )

        messages = [
            {"role": "system", "content": "You are a professional translator."},
            {"role": "user", "content": prompt},
        ]

        return self._provider.chat(messages)

    def _merge_pairs(self, pairs: List[ParagraphPair]) -> str:
        lines = []
        for pair in pairs:
            if pair.translated:
                lines.append(pair.translated)
        return "\n\n".join(lines)

    def translate_with对照(self, text: str, target_language: str = "zh") -> Tuple[str, List[ParagraphPair]]:
        if not text or not text.strip():
            return "", []

        paragraphs = self._split_into_paragraphs(text)
        pairs = self._translate_paragraphs(paragraphs, target_language)

        translated_text = self._merge_pairs(pairs)
        return translated_text, pairs

    def get_provider_name(self) -> str:
        return self._provider.get_name()