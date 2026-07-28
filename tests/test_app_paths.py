import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mercury.storage.app_paths import (
    application_data_directory,
    database_path,
)


class ApplicationPathTest(unittest.TestCase):
    def test_uses_cross_platform_user_data_directories(self) -> None:
        home = Path("/users/reader")

        self.assertEqual(
            application_data_directory(
                environment={"LOCALAPPDATA": "C:/Users/reader/AppData/Local"},
                platform="win32",
                home=home,
            ),
            Path("C:/Users/reader/AppData/Local") / "Mercury",
        )
        self.assertEqual(
            application_data_directory(
                environment={},
                platform="darwin",
                home=home,
            ),
            home / "Library" / "Application Support" / "Mercury",
        )
        self.assertEqual(
            application_data_directory(
                environment={"XDG_DATA_HOME": "/users/reader/.data"},
                platform="linux",
                home=home,
            ),
            Path("/users/reader/.data") / "Mercury",
        )

    def test_environment_override_is_supported(self) -> None:
        self.assertEqual(
            application_data_directory(
                environment={"MERCURY_DATA_DIR": "portable-data"},
                platform="win32",
                home=Path("/unused"),
            ),
            Path("portable-data"),
        )

    def test_migrates_legacy_database_without_overwriting_destination(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            legacy = root / "legacy" / "database.db"
            legacy.parent.mkdir()
            legacy.write_bytes(b"legacy database")
            data_directory = root / "local-data"
            environment = {"MERCURY_DATA_DIR": str(data_directory)}

            destination = database_path(
                legacy_paths=(legacy,),
                environment=environment,
            )

            self.assertEqual(destination, data_directory / "database.db")
            self.assertEqual(destination.read_bytes(), b"legacy database")

            destination.write_bytes(b"current database")
            legacy.write_bytes(b"changed legacy database")

            second_result = database_path(
                legacy_paths=(legacy,),
                environment=environment,
            )

            self.assertEqual(second_result, destination)
            self.assertEqual(destination.read_bytes(), b"current database")


if __name__ == "__main__":
    unittest.main()
