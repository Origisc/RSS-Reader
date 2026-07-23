from __future__ import annotations

from dataclasses import dataclass

from mercury.llm.provider import (
    LLMProvider,
    LLMProviderError,
    LLMRequest,
)


@dataclass
class TranslationResult:
    success: bool
    translated_text: str = ""
    error_message: str | None = None
    paragraph_count: int = 0
    failed_paragraphs: int = 0


@dataclass
class ParagraphPair:
    original: str
    translated: str
    success: bool
    error: str | None = None


class TranslationService:
    def __init__(self, provider: LLMProvider):
        self._provider = provider

    def translate(
        self,
        text: str,
        target_language: str = "zh",
    ) -> TranslationResult:
        if not text or not text.strip():
            return TranslationResult(
                success=False,
                error_message="Text content is empty",
            )

        paragraphs = self._split_into_paragraphs(text)
        if not paragraphs:
            return TranslationResult(
                success=False,
                error_message="No paragraphs to translate",
            )

        pairs = self._translate_paragraphs(paragraphs, target_language)
        translated_text = self._merge_pairs(pairs)

        failed_count = sum(1 for p in pairs if not p.success)
        success = failed_count == 0 or failed_count < len(pairs)

        if success and not translated_text.strip():
            return TranslationResult(
                success=False,
                error_message="Translated content is empty",
            )

        return TranslationResult(
            success=success,
            translated_text=translated_text,
            paragraph_count=len(paragraphs),
            failed_paragraphs=failed_count,
        )

    def _split_into_paragraphs(self, text: str) -> list[str]:
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

    def _translate_paragraphs(
        self,
        paragraphs: list[str],
        target_language: str,
    ) -> list[ParagraphPair]:
        pairs: list[ParagraphPair] = []
        for paragraph in paragraphs:
            if not paragraph.strip():
                pairs.append(
                    ParagraphPair(
                        original=paragraph,
                        translated="",
                        success=True,
                    )
                )
                continue

            success, translated, error = self._translate_single_paragraph(
                paragraph,
                target_language,
            )
            if success:
                pairs.append(
                    ParagraphPair(
                        original=paragraph,
                        translated=translated,
                        success=True,
                    )
                )
            else:
                pairs.append(
                    ParagraphPair(
                        original=paragraph,
                        translated=paragraph,
                        success=False,
                        error=error,
                    )
                )

        return pairs

    def _translate_single_paragraph(
        self,
        paragraph: str,
        target_language: str,
    ) -> tuple[bool, str, str | None]:
        prompt = (
            f"Translate the following text to {target_language}. "
            "Keep the original meaning and tone. "
            "Do not add any extra explanation or content. "
            "Only return the translated text.\n\n"
            f"Text: {paragraph}"
        )

        try:
            response = self._provider.complete(
                LLMRequest(
                    prompt=prompt,
                    system_prompt="You are a professional translator.",
                )
            )
        except LLMProviderError as exc:
            return False, "", str(exc)
        except Exception:
            return False, "", "Provider request failed."

        translated = response.text.strip()
        if not translated:
            return False, "", "Provider returned an empty translation."

        return True, translated, None

    def _merge_pairs(self, pairs: list[ParagraphPair]) -> str:
        lines: list[str] = []
        for pair in pairs:
            if pair.translated:
                lines.append(pair.translated)
        return "\n\n".join(lines)

    def translate_with_comparison(
        self,
        text: str,
        target_language: str = "zh",
    ) -> tuple[str, list[ParagraphPair]]:
        if not text or not text.strip():
            return "", []

        paragraphs = self._split_into_paragraphs(text)
        pairs = self._translate_paragraphs(paragraphs, target_language)

        translated_text = self._merge_pairs(pairs)
        return translated_text, pairs

    def translate_with对照(
        self,
        text: str,
        target_language: str = "zh",
    ) -> tuple[str, list[ParagraphPair]]:
        """Compatibility alias for the teammate service's original API."""
        return self.translate_with_comparison(text, target_language)

    def get_provider_name(self) -> str:
        return type(self._provider).__name__
