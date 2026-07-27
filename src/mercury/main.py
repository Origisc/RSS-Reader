import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

if __package__ in {None, ""}:
    for path in (PROJECT_ROOT, SRC_ROOT):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))

from PySide6.QtWidgets import QApplication

from core.database import DBManager
from domain.feed.use_cases import FeedUseCase
from mercury.agents import (
    SummaryAgent,
    TranslationAgent,
)
from mercury.llm import HTTPChatCompletionsProvider
from mercury.services.backend_article_service import BackendArticleService
from mercury.services.translation_service import TranslationService
from mercury.storage import (
    SQLiteProviderConfigStore,
    SQLiteSummaryResultStore,
    SQLiteTranslationResultStore,
)
from mercury.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    db_path = Path.cwd() / "database.db"
    db = DBManager(str(db_path))
    feed_use_case = FeedUseCase(db)
    provider_config_store = SQLiteProviderConfigStore(db_path)
    provider = HTTPChatCompletionsProvider(provider_config_store)
    translation_service = TranslationService(provider)
    article_service = BackendArticleService(db, feed_use_case, translation_service)
    summary_result_store = SQLiteSummaryResultStore(db_path)
    translation_result_store = SQLiteTranslationResultStore(db_path)
    summary_agent = SummaryAgent(provider, summary_result_store)
    translation_agent = TranslationAgent(
        provider,
        translation_result_store,
    )

    window = MainWindow(
        article_service,
        feed_deletion_service=article_service,
        provider_config_store=provider_config_store,
        provider_connection_tester=provider.test_config,
        summary_generator=summary_agent.summarize,
        summary_result_loader=summary_result_store.latest_for_article,
        translation_generator=translation_agent.translate,
        translation_result_loader=(
            translation_result_store.latest_for_article
        ),
    )
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
