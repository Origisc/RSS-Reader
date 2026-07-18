import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.i18n import Translator


class TranslatorTest(unittest.TestCase):
    def test_default_language_is_simplified_chinese(self) -> None:
        translator = Translator()

        self.assertEqual(translator.language, "zh_CN")
        self.assertEqual(translator.text("menu.file"), "文件")

    def test_can_switch_to_english(self) -> None:
        translator = Translator("en_US")

        self.assertEqual(translator.language, "en_US")
        self.assertEqual(translator.text("menu.file"), "File")

    def test_invalid_language_falls_back_to_default(self) -> None:
        translator = Translator("fr_FR")

        self.assertEqual(translator.language, "zh_CN")
        self.assertEqual(translator.text("menu.help"), "帮助")

    def test_missing_key_returns_key_name(self) -> None:
        translator = Translator("en_US")

        self.assertEqual(translator.text("missing.key"), "missing.key")

    def test_reader_view_messages_are_available_in_both_languages(self) -> None:
        for language in ("zh_CN", "en_US"):
            translator = Translator(language)

            self.assertNotEqual(
                translator.text("reader.view.cleaned_html"),
                "reader.view.cleaned_html",
            )
            self.assertIn(
                "{error}",
                translator.text("reader.status.fallback_error"),
            )

    def test_reader_style_settings_are_available_in_both_languages(self) -> None:
        for language in ("zh_CN", "en_US"):
            translator = Translator(language)

            for key in (
                "settings.reader_font_size",
                "settings.reader_line_height",
                "settings.reader_content_width",
            ):
                self.assertNotEqual(translator.text(key), key)

    def test_read_state_actions_are_available_in_both_languages(self) -> None:
        for language in ("zh_CN", "en_US"):
            translator = Translator(language)

            self.assertNotEqual(
                translator.text("action.mark_read"),
                "action.mark_read",
            )
            self.assertNotEqual(
                translator.text("action.mark_unread"),
                "action.mark_unread",
            )

    def test_feed_deletion_messages_are_available_in_both_languages(self) -> None:
        for language in ("zh_CN", "en_US"):
            translator = Translator(language)

            for key in (
                "action.delete_feed",
                "feed.delete_dialog.title",
                "feed.delete_unavailable",
                "feed.delete_failed",
                "status.delete_feed_started",
                "status.delete_feed_finished",
            ):
                self.assertNotEqual(translator.text(key), key)

            self.assertIn(
                "{title}",
                translator.text("feed.delete_dialog.body"),
            )

    def test_ai_settings_messages_are_available_in_both_languages(self) -> None:
        for language in ("zh_CN", "en_US"):
            translator = Translator(language)

            for key in (
                "action.ai_settings",
                "ai_settings.title",
                "ai_settings.base_url",
                "ai_settings.model",
                "ai_settings.api_key",
                "ai_settings.timeout",
                "ai_settings.privacy_notice",
                "ai_settings.test_connection",
                "ai_settings.invalid_config",
                "ai_settings.connection_unavailable",
                "ai_settings.connection_success",
                "ai_settings.connection_failed",
                "status.ai_settings_saved",
            ):
                self.assertNotEqual(translator.text(key), key)

    def test_summary_panel_messages_are_available_in_both_languages(self) -> None:
        for language in ("zh_CN", "en_US"):
            translator = Translator(language)

            for key in (
                "summary.language",
                "summary.language.same",
                "summary.detail",
                "summary.detail.brief",
                "summary.detail.standard",
                "summary.detail.detailed",
                "summary.custom_prompt",
                "summary.generate",
                "summary.regenerate",
                "summary.configure_ai",
                "summary.generated_at",
                "summary.status.no_article",
                "summary.status.unavailable",
                "summary.status.running",
                "summary.status.storage_warning",
                "summary.error.provider_not_configured",
                "summary.error.provider_failure",
                "summary.error.unexpected",
            ):
                self.assertNotEqual(translator.text(key), key)

            self.assertIn(
                "{time}",
                translator.text("summary.generated_at"),
            )
