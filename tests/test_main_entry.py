import sys
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
    def test_production_window_receives_deletion_adapter(self) -> None:
        with (
            patch("mercury.main.QApplication") as application_class,
            patch("mercury.main.DBManager") as database_class,
            patch("mercury.main.FeedUseCase") as use_case_class,
            patch(
                "mercury.main.BackendArticleService"
            ) as article_service_class,
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
        window_class.assert_called_once_with(
            article_service,
            feed_deletion_service=article_service,
        )
        window_class.return_value.show.assert_called_once_with()
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
