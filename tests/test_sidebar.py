import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QToolButton

from mercury.ui.sidebar import Sidebar


class SidebarTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.sidebar = Sidebar()
        self.sidebar.set_action_texts(
            add_feed="Add Feed",
            import_opml="Import OPML",
            refresh="Refresh",
            delete_feed="Delete selected Feed",
        )

    def tearDown(self) -> None:
        self.sidebar.close()
        self.sidebar.deleteLater()

    def test_plus_button_requests_add_feed(self) -> None:
        requests: list[str] = []
        self.sidebar.add_feed_requested.connect(
            lambda: requests.append("add")
        )

        self.sidebar.add_feed_button.click()

        self.assertEqual(requests, ["add"])
        self.assertEqual(
            self.sidebar.feed_menu_button.popupMode(),
            QToolButton.ToolButtonPopupMode.InstantPopup,
        )
        self.assertEqual(
            self.sidebar.feed_menu_button.arrowType(),
            Qt.ArrowType.DownArrow,
        )

    def test_dropdown_actions_emit_existing_feed_commands(self) -> None:
        requests: list[str] = []
        self.sidebar.add_feed_requested.connect(
            lambda: requests.append("add")
        )
        self.sidebar.import_opml_requested.connect(
            lambda: requests.append("import")
        )
        self.sidebar.refresh_requested.connect(
            lambda: requests.append("refresh")
        )

        self.sidebar.menu_add_feed_action.trigger()
        self.sidebar.menu_import_opml_action.trigger()
        self.sidebar.menu_refresh_action.trigger()

        self.assertEqual(requests, ["add", "import", "refresh"])
        self.assertEqual(self.sidebar.menu_add_feed_action.text(), "Add Feed")
        self.assertEqual(
            self.sidebar.menu_import_opml_action.text(),
            "Import OPML",
        )

    def test_delete_action_requires_and_emits_selected_feed(self) -> None:
        from mercury.models.article import Feed

        requests: list[str] = []
        self.sidebar.delete_feed_requested.connect(requests.append)
        self.sidebar.set_feeds([Feed(id="feed-1", title="Example")])

        self.assertFalse(self.sidebar.menu_delete_feed_action.isEnabled())

        self.sidebar.feed_list.setCurrentRow(0)
        self.sidebar.menu_delete_feed_action.trigger()

        self.assertTrue(self.sidebar.menu_delete_feed_action.isEnabled())
        self.assertEqual(requests, ["feed-1"])
        self.assertEqual(
            self.sidebar.menu_delete_feed_action.text(),
            "Delete selected Feed",
        )


if __name__ == "__main__":
    unittest.main()
