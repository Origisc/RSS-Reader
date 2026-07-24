import sys
import runpy
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_production_window_receives_backend_and_ai_adapters(self) -> None:
        with (
            patch("mercury.main.QApplication") as application_class,
            patch("mercury.main.DBManager") as database_class,
            patch("mercury.main.FeedUseCase") as use_case_class,
            patch(
                "mercury.main.BackendArticleService"
            ) as article_service_class,
            patch(
                "mercury.main.InMemoryProviderConfigStore"
            ) as config_store_class,
            patch(
                "mercury.main.HTTPChatCompletionsProvider"
            ) as provider_class,
            patch(
                "mercury.main.InMemorySummaryResultStore"
            ) as summary_store_class,
            patch(
                "mercury.main.InMemoryTranslationResultStore"
            ) as translation_store_class,
            patch("mercury.main.SummaryAgent") as summary_agent_class,
            patch(
                "mercury.main.TranslationAgent"
            ) as translation_agent_class,
            patch("mercury.main.MainWindow") as window_class,
        ):
            application_class.return_value.exec.return_value = 0
            article_service = article_service_class.return_value

            result = main()

        database = database_class.return_value
        use_case_class.assert_called_once_with(database)
        article_service_class.assert_called_once_with(
            database,
            use_case_class.return_value,
        )
        provider_class.assert_called_once_with(
            config_store_class.return_value
        )
        summary_agent_class.assert_called_once_with(
            provider_class.return_value,
            summary_store_class.return_value,
        )
        translation_agent_class.assert_called_once_with(
            provider_class.return_value,
            translation_store_class.return_value,
        )
        window_class.assert_called_once_with(
            article_service,
            feed_deletion_service=article_service,
            provider_config_store=config_store_class.return_value,
            provider_connection_tester=(
                provider_class.return_value.test_config
            ),
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
        )
        window_class.return_value.show.assert_called_once_with()
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
