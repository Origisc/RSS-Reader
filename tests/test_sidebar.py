import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QToolButton,
)

from mercury.ui.sidebar import (
    ALL_FEEDS_ID,
    FEED_ID_ROLE,
    STARRED_FEED_ID,
    Sidebar,
)
from mercury.models.tag import Tag


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
            self.sidebar.feed_menu_button.text(),
            "▾",
        )

    def test_feeds_and_tags_use_the_same_sidebar_space(self) -> None:
        self.sidebar.set_tags(
            [
                Tag(id="1", name="AI", article_count=2),
                Tag(id="2", name="Programming", article_count=1),
            ]
        )

        self.assertEqual(self.sidebar.pages.currentIndex(), 0)
        self.sidebar.tags_tab.click()

        self.assertEqual(self.sidebar.pages.currentIndex(), 1)
        self.assertTrue(self.sidebar.tags_tab.isChecked())
        self.assertEqual(self.sidebar.tag_list.count(), 2)
        self.assertEqual(
            self.sidebar.tag_list.horizontalScrollBarPolicy(),
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )

        self.sidebar.feeds_tab.click()
        self.assertEqual(self.sidebar.pages.currentIndex(), 0)

    def test_feed_list_uses_compact_elided_rows_without_horizontal_scroll(
        self,
    ) -> None:
        self.assertEqual(
            self.sidebar.feed_list.horizontalScrollBarPolicy(),
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.assertEqual(
            self.sidebar.feed_list.textElideMode(),
            Qt.TextElideMode.ElideRight,
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

        self.sidebar.select_feed("feed-1")
        self.sidebar.menu_delete_feed_action.trigger()

        self.assertTrue(self.sidebar.menu_delete_feed_action.isEnabled())
        self.assertEqual(requests, ["feed-1"])
        self.assertEqual(
            self.sidebar.menu_delete_feed_action.text(),
            "Delete selected Feed",
        )

    def test_delete_action_emits_all_selected_real_feeds(self) -> None:
        from mercury.models.article import Feed

        requests: list[tuple[str, ...]] = []
        self.sidebar.delete_feeds_requested.connect(requests.append)
        self.sidebar.set_feeds(
            [
                Feed(id="feed-1", title="First"),
                Feed(id="feed-2", title="Second"),
                Feed(id="feed-3", title="Third"),
            ]
        )
        self.assertEqual(
            self.sidebar.feed_list.selectionMode(),
            QAbstractItemView.SelectionMode.SingleSelection,
        )

        self.sidebar.resize(360, 500)
        self.sidebar.show()
        self.app.processEvents()
        self.sidebar.batch_delete_button.click()
        self.assertEqual(
            self.sidebar.feed_list.selectionMode(),
            QAbstractItemView.SelectionMode.MultiSelection,
        )
        self.assertFalse(self.sidebar.menu_delete_feed_action.isEnabled())

        virtual_item = self.sidebar.feed_list.item(0)
        QTest.mouseClick(
            self.sidebar.feed_list.viewport(),
            Qt.MouseButton.LeftButton,
            pos=self.sidebar.feed_list.visualItemRect(
                virtual_item
            ).center(),
        )
        self.assertEqual(self.sidebar.selected_feed_ids(), ())
        self.assertFalse(self.sidebar.batch_delete_button.isEnabled())

        for feed_id in ("feed-1", "feed-3"):
            item = next(
                self.sidebar.feed_list.item(row)
                for row in range(self.sidebar.feed_list.count())
                if self.sidebar.feed_list.item(row).data(FEED_ID_ROLE)
                == feed_id
            )
            QTest.mouseClick(
                self.sidebar.feed_list.viewport(),
                Qt.MouseButton.LeftButton,
                pos=self.sidebar.feed_list.visualItemRect(item).center(),
            )

        self.assertEqual(
            self.sidebar.batch_delete_button.text(),
            "Delete selected (2)",
        )
        self.sidebar.batch_delete_button.click()

        self.assertEqual(requests, [("feed-1", "feed-3")])
        self.assertEqual(
            self.sidebar.selected_feed_ids(),
            ("feed-1", "feed-3"),
        )

    def test_batch_delete_mode_can_be_cancelled(self) -> None:
        from mercury.models.article import Feed

        self.sidebar.set_feeds(
            [
                Feed(id="feed-1", title="First"),
                Feed(id="feed-2", title="Second"),
            ]
        )
        self.sidebar.select_feed("feed-1")

        self.sidebar.batch_delete_button.click()
        second_item = next(
            self.sidebar.feed_list.item(row)
            for row in range(self.sidebar.feed_list.count())
            if self.sidebar.feed_list.item(row).data(FEED_ID_ROLE)
            == "feed-2"
        )
        second_item.setSelected(True)
        self.sidebar.cancel_batch_delete_button.click()

        self.assertEqual(
            self.sidebar.feed_list.selectionMode(),
            QAbstractItemView.SelectionMode.SingleSelection,
        )
        self.assertTrue(
            self.sidebar.cancel_batch_delete_button.isHidden()
        )
        self.assertEqual(
            self.sidebar.batch_delete_button.text(),
            "Select multiple",
        )
        self.assertEqual(self.sidebar.current_feed_id(), "feed-1")

    def test_context_menu_delete_targets_the_clicked_feed(self) -> None:
        from mercury.models.article import Feed

        requests: list[str] = []
        self.sidebar.delete_feed_requested.connect(requests.append)
        self.sidebar.set_feeds(
            [
                Feed(id="feed-1", title="First"),
                Feed(id="feed-2", title="Second"),
            ]
        )

        second_feed_item = next(
            self.sidebar.feed_list.item(row)
            for row in range(self.sidebar.feed_list.count())
            if self.sidebar.feed_list.item(row).data(FEED_ID_ROLE)
            == "feed-2"
        )
        menu = self.sidebar._build_feed_context_menu(second_feed_item)
        delete_action = menu.actions()[0]
        delete_action.trigger()

        self.assertEqual(requests, ["feed-2"])
        self.assertEqual(delete_action.text(), "Delete selected Feed")
        self.assertEqual(
            delete_action.objectName(),
            "ContextDeleteFeedAction",
        )
        self.assertEqual(
            self.sidebar.feed_list.contextMenuPolicy(),
            Qt.ContextMenuPolicy.CustomContextMenu,
        )

    def test_virtual_all_and_starred_rows_precede_real_feeds(self) -> None:
        from mercury.models.article import Feed

        self.sidebar.set_virtual_feed_texts(
            all_feeds="All Feeds",
            starred="Starred",
            starred_detail="{count}",
        )
        self.sidebar.set_feeds(
            [Feed(id="feed-1", title="Example")],
            {"feed-1": 2},
            starred_count=3,
        )

        self.assertEqual(
            self.sidebar.feed_list.item(0).data(FEED_ID_ROLE),
            ALL_FEEDS_ID,
        )
        self.assertEqual(
            self.sidebar.feed_list.item(1).data(FEED_ID_ROLE),
            STARRED_FEED_ID,
        )
        self.assertIn("3", self.sidebar.feed_list.item(1).text())
        self.assertFalse(self.sidebar.feed_list.item(1).icon().isNull())

    def test_virtual_rows_emit_selection_but_cannot_be_deleted(self) -> None:
        from mercury.models.article import Feed

        selections: list[str] = []
        deletions: list[str] = []
        self.sidebar.feed_selected.connect(selections.append)
        self.sidebar.delete_feed_requested.connect(deletions.append)
        self.sidebar.set_feeds([Feed(id="feed-1", title="Example")])

        self.sidebar.select_feed(STARRED_FEED_ID)
        self.sidebar.menu_delete_feed_action.trigger()

        self.assertEqual(selections, [STARRED_FEED_ID])
        self.assertFalse(self.sidebar.menu_delete_feed_action.isEnabled())
        self.assertEqual(deletions, [])

    def test_context_menu_is_not_built_for_blank_space(self) -> None:
        with patch.object(
            self.sidebar,
            "_build_feed_context_menu",
        ) as build_menu:
            self.sidebar._show_feed_context_menu(QPoint(-1, -1))

        build_menu.assert_not_called()


if __name__ == "__main__":
    unittest.main()
