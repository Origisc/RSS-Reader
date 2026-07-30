import sys
import runpy
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

for path in (PROJECT_ROOT, SRC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from mercury.main import main


class MainEntryTest(unittest.TestCase):
    def test_root_script_delegates_to_current_source_entry(self) -> None:
        with patch("mercury.main.main", return_value=17) as source_main:
            with self.assertRaises(SystemExit) as context:
                runpy.run_path(
                    PROJECT_ROOT / "main.py",
                    run_name="__main__",
                )

        source_main.assert_called_once_with()
        self.assertEqual(context.exception.code, 17)

    def test_startup_reports_unwritable_local_data_directory(self) -> None:
        with (
            patch("mercury.main.QApplication") as application_class,
            patch(
                "mercury.main.database_path",
                side_effect=OSError("permission denied"),
            ),
            patch("mercury.main.QMessageBox") as message_box,
            patch("mercury.main.DBManager") as database_class,
        ):
            result = main()

        self.assertEqual(result, 1)
        database_class.assert_not_called()
        application_class.return_value.exec.assert_not_called()
        message_box.critical.assert_called_once()
        error_message = message_box.critical.call_args.args[2]
        self.assertIn("无法初始化本地数据目录", error_message)
        self.assertIn("could not initialize", error_message)

    def test_production_window_receives_backend_and_ai_adapters(self) -> None:
        with (
            patch("mercury.main.QApplication") as application_class,
            patch("mercury.main.DBManager") as database_class,
            patch("mercury.main.FeedUseCase") as use_case_class,
            patch(
                "mercury.main.BackendArticleService"
            ) as article_service_class,
            patch(
                "mercury.main.SQLiteProviderConfigStore"
            ) as config_store_class,
            patch(
                "mercury.main.HTTPChatCompletionsProvider"
            ) as provider_class,
            patch(
                "mercury.main.TranslationService"
            ) as translation_service_class,
            patch(
                "mercury.main.SQLiteSummaryResultStore"
            ) as summary_store_class,
            patch(
                "mercury.main.SQLiteTranslationResultStore"
            ) as translation_store_class,
            patch(
                "mercury.main.QSettingsBilingualViewStateStore"
            ) as bilingual_state_store_class,
            patch(
                "mercury.main.database_path",
                return_value=Path("local-data") / "database.db",
            ) as database_path_function,
            patch("mercury.main.SummaryAgent") as summary_agent_class,
            patch("mercury.main.TagAgent") as tag_agent_class,
            patch(
                "mercury.main.TranslationAgent"
            ) as translation_agent_class,
            patch("mercury.main.MainWindow") as window_class,
        ):
            application_class.return_value.exec.return_value = 0
            article_service = article_service_class.return_value
            config_stores = [MagicMock() for _ in range(3)]
            providers = [MagicMock() for _ in range(3)]
            config_store_class.side_effect = config_stores
            provider_class.side_effect = providers

            result = main()

        database = database_class.return_value
        database_path = Path("local-data") / "database.db"
        database_path_function.assert_called_once_with(
            legacy_paths=(
                Path.cwd() / "database.db",
                PROJECT_ROOT / "database.db",
            ),
        )
        application_class.return_value.setApplicationName.assert_called_once_with(
            "Mercury"
        )
        application_class.return_value.setOrganizationName.assert_called_once_with(
            "Mercury"
        )
        application_class.return_value.setFont.assert_called_once()
        use_case_class.assert_called_once_with(database)
        article_service_class.assert_called_once_with(
            database,
            use_case_class.return_value,
            translation_service_class.return_value,
        )
        self.assertEqual(
            config_store_class.call_args_list,
            [
                call(database_path, profile="summary"),
                call(database_path, profile="translation"),
                call(database_path, profile="tag"),
            ],
        )
        self.assertEqual(
            provider_class.call_args_list,
            [call(store) for store in config_stores],
        )
        translation_service_class.assert_called_once_with(
            providers[1]
        )
        summary_store_class.assert_called_once_with(database_path)
        translation_store_class.assert_called_once_with(database_path)
        summary_agent_class.assert_called_once_with(
            providers[0],
            summary_store_class.return_value,
        )
        tag_agent_class.assert_called_once_with(
            providers[2]
        )
        translation_agent_class.assert_called_once_with(
            providers[1],
            translation_store_class.return_value,
        )
        bilingual_state_store_class.assert_called_once_with()
        window_class.assert_called_once_with(
            article_service,
            bilingual_view_state_store=(
                bilingual_state_store_class.return_value
            ),
            feed_deletion_service=article_service,
            agent_provider_config_stores={
                "summary": config_stores[0],
                "translation": config_stores[1],
                "tag": config_stores[2],
            },
            agent_connection_testers={
                "summary": providers[0].test_config,
                "translation": providers[1].test_config,
                "tag": providers[2].test_config,
            },
            summary_generator=(
                summary_agent_class.return_value.summarize
            ),
            summary_result_loader=(
                summary_store_class.return_value.latest_for_article
            ),
            translation_generator=(
                translation_agent_class.return_value.translate
            ),
            translation_result_loader=(
                translation_store_class.return_value.latest_for_article
            ),
            tag_suggestion_generator=(
                tag_agent_class.return_value.suggest
            ),
        )
        window_class.return_value.show.assert_called_once_with()
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
