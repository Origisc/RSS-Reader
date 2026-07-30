import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtCore import QSettings

from mercury.ui.bilingual_state import (
    InMemoryBilingualViewStateStore,
    QSettingsBilingualViewStateStore,
)


class BilingualViewStateStoreTest(unittest.TestCase):
    def test_in_memory_store_distinguishes_missing_false_and_true(self) -> None:
        store = InMemoryBilingualViewStateStore()

        self.assertIsNone(store.load("article-1"))

        store.save("article-1", False)
        store.save("article-2", True)

        self.assertIs(store.load("article-1"), False)
        self.assertIs(store.load("article-2"), True)

    def test_qsettings_store_survives_reopen_with_utf8_article_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            settings_path = (
                Path(temporary_directory) / "reader-preferences.ini"
            )
            first_settings = QSettings(
                str(settings_path),
                QSettings.Format.IniFormat,
            )
            first_store = QSettingsBilingualViewStateStore(first_settings)
            article_id = "feed/安全文章-1"

            self.assertIsNone(first_store.load(article_id))
            first_store.save(article_id, False)

            reopened_settings = QSettings(
                str(settings_path),
                QSettings.Format.IniFormat,
            )
            reopened_store = QSettingsBilingualViewStateStore(
                reopened_settings
            )

            self.assertIs(reopened_store.load(article_id), False)
            reopened_store.save(article_id, True)
            self.assertIs(reopened_store.load(article_id), True)


if __name__ == "__main__":
    unittest.main()
