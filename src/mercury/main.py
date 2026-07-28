import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

if __package__ in {None, ""}:
    for path in (PROJECT_ROOT, SRC_ROOT):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))

from PySide6.QtWidgets import QApplication, QMessageBox

from core.database import DBManager
from domain.feed.use_cases import FeedUseCase
from mercury.agents import (
    SummaryAgent,
    TagAgent,
    TranslationAgent,
)
from mercury.llm import HTTPChatCompletionsProvider
from mercury.services.backend_article_service import BackendArticleService
from mercury.services.translation_service import TranslationService
from mercury.storage import (
    SQLiteProviderConfigStore,
    SQLiteSummaryResultStore,
    SQLiteTranslationResultStore,
    database_path,
)
from mercury.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Mercury")
    app.setOrganizationName("Mercury")

    legacy_database_paths = (
        Path.cwd() / "database.db",
        PROJECT_ROOT / "database.db",
    )
    try:
        db_path = database_path(legacy_paths=legacy_database_paths)
        db = DBManager(str(db_path))
        feed_use_case = FeedUseCase(db)
        provider_config_stores = {
            agent_id: SQLiteProviderConfigStore(db_path, profile=agent_id)
            for agent_id in ("summary", "translation", "tag")
        }
        providers = {
            agent_id: HTTPChatCompletionsProvider(config_store)
            for agent_id, config_store in provider_config_stores.items()
        }
        translation_service = TranslationService(providers["translation"])
        article_service = BackendArticleService(
            db,
            feed_use_case,
            translation_service,
        )
        summary_result_store = SQLiteSummaryResultStore(db_path)
        translation_result_store = SQLiteTranslationResultStore(db_path)
    except (OSError, sqlite3.Error) as exc:
        QMessageBox.critical(
            None,
            "Mercury",
            "Mercury 无法初始化本地数据目录，程序尚未修改任何订阅数据。\n\n"
            "Mercury could not initialize its local data directory. "
            "No subscription data was changed.\n\n"
            f"{exc}",
        )
        return 1
    summary_agent = SummaryAgent(
        providers["summary"],
        summary_result_store,
    )
    tag_agent = TagAgent(providers["tag"])
    translation_agent = TranslationAgent(
        providers["translation"],
        translation_result_store,
    )

    window = MainWindow(
        article_service,
        feed_deletion_service=article_service,
        agent_provider_config_stores=provider_config_stores,
        agent_connection_testers={
            agent_id: provider.test_config
            for agent_id, provider in providers.items()
        },
        summary_generator=summary_agent.summarize,
        summary_result_loader=summary_result_store.latest_for_article,
        translation_generator=translation_agent.translate,
        translation_result_loader=(
            translation_result_store.latest_for_article
        ),
        tag_suggestion_generator=tag_agent.suggest,
    )
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
