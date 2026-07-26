import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

for path in (PROJECT_ROOT, SRC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from core.database import DBManager
from domain.feed.use_cases import FeedUseCase
from mercury.models.tag import Tag
from mercury.services.backend_article_service import BackendArticleService
from mercury.services.mock_article_service import MockArticleService
from mercury.services.tag_service import TagServiceError
from mercury.ui.main_window import MainWindow
from mercury.ui.sidebar import Sidebar
from mercury.ui.tag_panel import TagEditorPanel


class TagPersistenceTest(unittest.TestCase):
    def _service_with_articles(
        self,
        database: DBManager,
    ) -> tuple[BackendArticleService, str, str, int]:
        feed_id = int(
            database.add_feed(
                "Example",
                "https://example.com/feed",
            )
        )
        database.save_articles(
            feed_id,
            [
                {
                    "title": "First",
                    "link": "https://example.com/first",
                    "published": "2026-07-26T12:00:00",
                },
                {
                    "title": "Second",
                    "link": "https://example.com/second",
                    "published": "2026-07-26T11:00:00",
                },
            ],
        )
        article_ids = [
            str(row[0])
            for row in database.get_articles_by_feed(feed_id)
        ]
        return (
            BackendArticleService(database, FeedUseCase(database)),
            article_ids[0],
            article_ids[1],
            feed_id,
        )

    def test_schema_and_tag_assignment_survive_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "tags.db"
            first = DBManager(str(database_path))
            service, first_id, _second_id, _feed_id = (
                self._service_with_articles(first)
            )
            tag = service.create_tag("  Local   First  ")
            service.add_tag_to_article(first_id, tag.id)
            first.conn.close()

            second = DBManager(str(database_path))
            try:
                tables = {
                    row[0]
                    for row in second.conn.execute(
                        "SELECT name FROM sqlite_master "
                        "WHERE type = 'table'"
                    )
                }
                self.assertTrue({"tags", "article_tags"}.issubset(tables))
                self.assertEqual(
                    second.list_tags(),
                    [(int(tag.id), "Local First", 1)],
                )
                self.assertEqual(
                    second.get_article_tags(int(first_id)),
                    [(int(tag.id), "Local First")],
                )
            finally:
                second.conn.close()

    def test_case_insensitive_create_is_idempotent(self) -> None:
        database = DBManager(":memory:")
        service, _first_id, _second_id, _feed_id = (
            self._service_with_articles(database)
        )
        try:
            first = service.create_tag("Python")
            second = service.create_tag("python")

            self.assertEqual(first.id, second.id)
            self.assertEqual(len(service.list_tags()), 1)
        finally:
            database.conn.close()

    def test_multiple_tag_filter_uses_and_semantics(self) -> None:
        database = DBManager(":memory:")
        service, first_id, second_id, _feed_id = (
            self._service_with_articles(database)
        )
        try:
            python = service.create_tag("Python")
            local = service.create_tag("Local")
            service.add_tag_to_article(first_id, python.id)
            service.add_tag_to_article(first_id, local.id)
            service.add_tag_to_article(second_id, python.id)

            self.assertEqual(
                {
                    article.id
                    for article in service.list_articles_by_tags(
                        [python.id]
                    )
                },
                {first_id, second_id},
            )
            self.assertEqual(
                [
                    article.id
                    for article in service.list_articles_by_tags(
                        [python.id, local.id]
                    )
                ],
                [first_id],
            )
        finally:
            database.conn.close()

    def test_rename_conflict_and_delete_cascade_are_safe(self) -> None:
        database = DBManager(":memory:")
        service, first_id, _second_id, feed_id = (
            self._service_with_articles(database)
        )
        try:
            first = service.create_tag("First")
            second = service.create_tag("Second")
            service.add_tag_to_article(first_id, first.id)

            with self.assertRaises(TagServiceError):
                service.rename_tag(second.id, "first")

            service.delete_tag(first.id)
            self.assertEqual(service.list_article_tags(first_id), [])

            service.add_tag_to_article(first_id, second.id)
            self.assertTrue(database.delete_feed(feed_id))
            self.assertEqual(
                database.conn.execute(
                    "SELECT COUNT(*) FROM article_tags"
                ).fetchone()[0],
                0,
            )
            self.assertEqual(service.list_tags()[0].article_count, 0)
        finally:
            database.conn.close()


class TagServiceTest(unittest.TestCase):
    def test_mock_service_validates_and_filters_tags(self) -> None:
        service = MockArticleService()
        python = service.create_tag("Python")
        local = service.create_tag("Local")
        service.add_tag_to_article("mercury-start", python.id)
        service.add_tag_to_article("mercury-start", local.id)
        service.add_tag_to_article("pyside-layout", python.id)

        self.assertEqual(
            [
                article.id
                for article in service.list_articles_by_tags(
                    [python.id, local.id]
                )
            ],
            ["mercury-start"],
        )
        self.assertEqual(
            next(
                tag for tag in service.list_tags() if tag.id == python.id
            ).article_count,
            2,
        )
        with self.assertRaises(TagServiceError):
            service.create_tag(" ")
        with self.assertRaises(TagServiceError):
            service.add_tag_to_article("missing", python.id)


class TagUITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_editor_emits_create_and_assignment_requests(self) -> None:
        panel = TagEditorPanel()
        panel.set_texts(
            title="Tags",
            input_placeholder="Tags",
            add="Add",
            existing="Existing",
            empty="Empty",
            no_article="Select an article",
            close_tooltip="Close",
        )
        panel.set_article_tags(
            [Tag(id="1", name="Python")],
            set(),
            article_available=True,
        )
        additions: list[str] = []
        assignments: list[tuple[str, bool]] = []
        panel.add_tag_requested.connect(additions.append)
        panel.tag_assignment_changed.connect(
            lambda tag_id, checked: assignments.append(
                (tag_id, checked)
            )
        )

        panel.tag_input.setText("Local")
        panel.add_button.click()
        panel.chip_grid.itemAt(0).widget().click()

        self.assertEqual(additions, ["Local"])
        self.assertEqual(assignments, [("1", True)])
        panel.close()
        panel.deleteLater()

    def test_sidebar_emits_combined_tag_filter(self) -> None:
        sidebar = Sidebar()
        sidebar.set_tags(
            [
                Tag(id="1", name="Python", article_count=2),
                Tag(id="2", name="Local", article_count=1),
            ]
        )
        selections: list[tuple[str, ...]] = []
        sidebar.tag_filter_changed.connect(selections.append)

        sidebar.tag_list.item(0).setCheckState(Qt.CheckState.Checked)
        sidebar.tag_list.item(1).setCheckState(Qt.CheckState.Checked)

        self.assertEqual(selections[-1], ("1", "2"))
        self.assertTrue(sidebar.clear_tag_filter_button.isEnabled())
        sidebar.clear_tag_filter()
        self.assertEqual(selections[-1], ())
        sidebar.close()
        sidebar.deleteLater()

    def test_main_window_creates_assigns_and_filters_local_tags(self) -> None:
        service = MockArticleService()
        window = MainWindow(service)
        window._show_article("mercury-start")

        window.tag_editor.tag_input.setText("Python, Local")
        window.tag_editor.add_button.click()

        assigned = service.list_article_tags("mercury-start")
        self.assertEqual(
            {tag.name for tag in assigned},
            {"Python", "Local"},
        )
        python = next(
            tag for tag in service.list_tags() if tag.name == "Python"
        )
        service.add_tag_to_article("pyside-layout", python.id)
        window._reload_tags()
        python_row = next(
            row
            for row in range(window.sidebar.tag_list.count())
            if window.sidebar.tag_list.item(row).text().startswith(
                "Python"
            )
        )

        window.sidebar.tag_list.item(python_row).setCheckState(
            Qt.CheckState.Checked
        )

        self.assertEqual(
            set(window.article_list.visible_article_ids()),
            {"mercury-start", "pyside-layout"},
        )
        self.assertIn("Python", window.article_list.title_label.text())
        window.close()
        window.deleteLater()
        self.app.setStyleSheet("")

    def test_tag_deletion_requires_confirmation_and_keeps_articles(self) -> None:
        service = MockArticleService()
        tag = service.create_tag("Keep me")
        service.add_tag_to_article("mercury-start", tag.id)
        window = MainWindow(service)

        with patch.object(
            window,
            "_confirm_tag_deletion",
            return_value=False,
        ):
            window._delete_tag(tag.id)

        self.assertEqual(len(service.list_tags()), 1)
        self.assertIsNotNone(service.get_article("mercury-start"))

        with patch.object(
            window,
            "_confirm_tag_deletion",
            return_value=True,
        ):
            window._delete_tag(tag.id)

        self.assertEqual(service.list_tags(), [])
        self.assertIsNotNone(service.get_article("mercury-start"))
        window.close()
        window.deleteLater()
        self.app.setStyleSheet("")


if __name__ == "__main__":
    unittest.main()
