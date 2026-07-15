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
from mercury.services.backend_article_service import BackendArticleService
from mercury.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    db_path = Path.cwd() / "database.db"
    db = DBManager(str(db_path))
    feed_use_case = FeedUseCase(db)
    article_service = BackendArticleService(db, feed_use_case)

    window = MainWindow(article_service)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())