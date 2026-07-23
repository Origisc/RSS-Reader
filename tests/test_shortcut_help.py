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

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QDialogButtonBox

from mercury.i18n import Translator
from mercury.services.mock_article_service import MockArticleService
from mercury.ui.main_window import MainWindow
from mercury.ui.shortcut_help import ShortcutEntry, ShortcutHelpDialog


class ShortcutHelpDialogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_dialog_lists_shortcuts_and_functions(self) -> None:
        translator = Translator("zh_CN")
        entries = (
            ShortcutEntry("F1", "打开快捷键说明"),
            ShortcutEntry("Ctrl+Q", "退出 Mercury"),
        )
        dialog = ShortcutHelpDialog(translator, entries)

        self.assertEqual(dialog.windowTitle(), "键盘快捷键")
        self.assertEqual(dialog.table.rowCount(), 2)
        self.assertEqual(dialog.table.item(0, 0).text(), "F1")
        self.assertEqual(dialog.table.item(1, 1).text(), "退出 Mercury")
        self.assertEqual(
            dialog.button_box.button(
                QDialogButtonBox.StandardButton.Close
            ).text(),
            "关闭",
        )
        dialog.close()
        dialog.deleteLater()

    def test_help_menu_action_opens_complete_shortcut_reference(self) -> None:
        window = MainWindow(MockArticleService())

        self.assertIn(
            window.shortcut_help_action,
            window.help_menu.actions(),
        )
        self.assertEqual(
            window.shortcut_help_action.shortcut().toString(),
            "F1",
        )
        self.assertEqual(
            {entry.key for entry in window._shortcut_entries()},
            {"F1", "Ctrl+,", "Ctrl+Shift+S", "Ctrl+Q"},
        )

        with patch.object(ShortcutHelpDialog, "exec", return_value=0) as exec_mock:
            window.shortcut_help_action.trigger()

        exec_mock.assert_called_once_with()
        window.close()
        window.deleteLater()

    def test_new_action_shortcut_is_discovered_automatically(self) -> None:
        window = MainWindow(MockArticleService())
        new_action = QAction("New feature", window)
        new_action.setShortcut("Ctrl+Alt+N")
        new_action.setStatusTip("Run the new feature")

        entries = {
            entry.key: entry.description
            for entry in window._shortcut_entries()
        }

        self.assertEqual(entries["Ctrl+Alt+N"], "Run the new feature")
        window.close()
        window.deleteLater()


if __name__ == "__main__":
    unittest.main()
