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
            self.assertNotEqual(
                translator.text("reader.tags_toggle"),
                "reader.tags_toggle",
            )
            self.assertNotEqual(
                translator.text("article_list.unread_filter"),
                "article_list.unread_filter",
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
                "action.delete_feeds",
                "action.multi_select_feeds",
                "action.delete_selected_feeds",
                "feed.delete_dialog.title",
                "feed.delete_many_dialog.title",
                "feed.delete_unavailable",
                "feed.delete_failed",
                "feed.delete_many_failed",
                "status.delete_feed_started",
                "status.delete_feed_finished",
                "status.delete_feeds_started",
                "status.delete_feeds_finished",
            ):
                self.assertNotEqual(translator.text(key), key)

            self.assertIn(
                "{title}",
                translator.text("feed.delete_dialog.body"),
            )
            self.assertIn(
                "{count}",
                translator.text("feed.delete_many_dialog.body"),
            )
            self.assertIn(
                "{titles}",
                translator.text("feed.delete_many_dialog.body"),
            )
            self.assertIn(
                "{count}",
                translator.text("action.delete_selected_feeds"),
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
                "agents_settings.title",
                "agents_settings.properties",
                "agents_settings.enabled",
                "agents_settings.save",
                "agents_settings.agent.summary",
                "agents_settings.agent.translation",
                "agents_settings.agent.tag",
                "status.ai_settings_saved",
                "status.ai_settings_storage_failed",
            ):
                self.assertNotEqual(translator.text(key), key)

    def test_starred_entry_messages_are_available_in_both_languages(
        self,
    ) -> None:
        for language in ("zh_CN", "en_US"):
            translator = Translator(language)

            for key in (
                "action.star",
                "action.unstar",
                "sidebar.all_feeds",
                "sidebar.starred",
                "sidebar.starred_detail",
                "article_list.starred_title",
                "status.article_starred",
                "status.article_unstarred",
                "status.star_failed",
            ):
                self.assertNotEqual(translator.text(key), key)

    def test_manual_tag_messages_are_available_in_both_languages(
        self,
    ) -> None:
        for language in ("zh_CN", "en_US"):
            translator = Translator(language)

            for key in (
                "article_list.tags_title",
                "tags.existing",
                "tags.empty",
                "tags.no_article",
                "tags.filter_clear",
                "tags.rename",
                "tags.delete",
                "tags.rename_dialog.title",
                "tags.rename_dialog.label",
                "tags.delete_dialog.title",
                "status.tags_added",
                "status.tag_assigned",
                "status.tag_removed",
                "status.tag_renamed",
                "status.tag_deleted",
                "status.tag_failed",
            ):
                self.assertNotEqual(translator.text(key), key)

            self.assertIn(
                "{name}",
                translator.text("tags.delete_dialog.body"),
            )

    def test_tag_agent_messages_are_available_in_both_languages(self) -> None:
        for language in ("zh_CN", "en_US"):
            translator = Translator(language)

            for key in (
                "tag_agent.title",
                "tag_agent.custom_prompt_placeholder",
                "tag_agent.generate",
                "tag_agent.configure_ai",
                "tag_agent.apply",
                "tag_agent.dismiss",
                "tag_agent.status.no_article",
                "tag_agent.status.unavailable",
                "tag_agent.status.ready",
                "tag_agent.status.running",
                "tag_agent.status.generated",
                "tag_agent.error.invalid_input",
                "tag_agent.error.provider_not_configured",
                "tag_agent.error.provider_failure",
                "tag_agent.error.empty_response",
                "tag_agent.error.unexpected",
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
                "summary.generate_tooltip.no_article",
                "summary.generate_tooltip.configure",
                "summary.generate_tooltip.ready",
                "summary.configure_ai",
                "summary.generated_at",
                "summary.status.no_article",
                "summary.status.unavailable",
                "summary.status.running",
                "summary.status.storage_warning",
                "summary.error.provider_not_configured",
                "summary.error.provider_failure",
                "summary.error.wrong_language",
                "summary.error.unexpected",
            ):
                self.assertNotEqual(translator.text(key), key)

            self.assertNotEqual(
                translator.text("action.toggle_summary_panel"),
                "action.toggle_summary_panel",
            )
            self.assertNotEqual(
                translator.text("reader.summary_toggle"),
                "reader.summary_toggle",
            )
            self.assertNotEqual(
                translator.text("summary.hide_panel"),
                "summary.hide_panel",
            )
            self.assertNotEqual(
                translator.text("summary.hide_panel_tooltip"),
                "summary.hide_panel_tooltip",
            )
            self.assertNotEqual(
                translator.text("action.shortcuts"),
                "action.shortcuts",
            )
            self.assertNotEqual(
                translator.text("shortcuts.title"),
                "shortcuts.title",
            )
            self.assertNotEqual(
                translator.text("shortcuts.toggle_summary"),
                "shortcuts.toggle_summary",
            )
            self.assertIn(
                "Ctrl+Shift+S",
                translator.text("reader.summary_toggle_tooltip"),
            )

            self.assertIn(
                "{time}",
                translator.text("summary.generated_at"),
            )

    def test_translation_validation_errors_are_localized(self) -> None:
        for language in ("zh_CN", "en_US"):
            translator = Translator(language)

            for key in (
                "translation.error.wrong_language",
                "translation.error.incomplete_response",
            ):
                self.assertNotEqual(translator.text(key), key)
