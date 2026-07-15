import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication

from mercury.services.mock_article_service import MockArticleService
from mercury.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    article_service = MockArticleService()
    window = MainWindow(article_service)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())