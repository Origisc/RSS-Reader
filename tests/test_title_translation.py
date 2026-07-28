import os
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtWidgets import QApplication, QMessageBox

from mercury.services.mock_article_service import MockArticleService
from mercury.ui.main_window import MainWindow


class ImmediateThreadPool:
    def start(self, worker) -> None:
        worker.run()


class TranslatableMockArticleService(MockArticleService):
    def __init__(self) -> None:
        super().__init__()
        self.translated_ids: list[str] = []

    def translate_article_title(
        self,
        article_id: str,
        target_language: str = "zh",
        force: bool = False,
    ) -> str:
        del force
        self.translated_ids.append(article_id)
        self._articles = [
            (
                replace(
                    article,
                    translated_title=f"译文：{article.title}",
                )
                if article.id == article_id
                else article
            )
            for article in self._articles
        ]
        return (
            f"Article title translated to {target_language} successfully."
        )


class TitleTranslationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_batch_translates_visible_untranslated_entry_titles_only(
        self,
    ) -> None:
        service = TranslatableMockArticleService()
        first_article = service._articles[0]
        service._articles[0] = replace(
            first_article,
            translated_title="已有译文",
        )
        window = MainWindow(service)
        article_ids = tuple(window.article_list.visible_article_ids())
        displayed_id = article_ids[1]
        displayed_article = service.get_article(displayed_id)
        window.article_list.select_article(displayed_id)
        self.app.processEvents()

        with (
            patch(
                "mercury.ui.main_window.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Yes,
            ) as question,
            patch(
                "mercury.ui.main_window.QThreadPool.globalInstance",
                return_value=ImmediateThreadPool(),
            ),
        ):
            window._translate_visible_article_titles(article_ids)

        self.assertEqual(
            service.translated_ids,
            list(article_ids[1:]),
        )
        self.assertIn(
            "2",
            question.call_args.args[2],
        )
        entry_text = "\n".join(
            window.article_list.list_widget.item(row).text()
            for row in range(window.article_list.list_widget.count())
        )
        self.assertIn("已有译文", entry_text)
        self.assertIn("译文：", entry_text)
        self.assertIsNotNone(displayed_article)
        self.assertIn(
            displayed_article.title,
            window.article_reader.content.toPlainText(),
        )
        self.assertNotIn(
            f"译文：{displayed_article.title}",
            window.article_reader.content.toPlainText(),
        )
        self.assertIn("成功 2 个", window.statusBar().currentMessage())
        self.assertFalse(
            any(
                type(worker).__name__ == "_TitleBatchTranslator"
                for worker in window._active_workers
            )
        )

        provider_calls = list(service.translated_ids)
        window._clear_title_translation(displayed_id)

        self.assertEqual(
            service.get_article(displayed_id).translated_title,
            "",
        )
        self.assertEqual(service.translated_ids, provider_calls)
        self.assertIn(
            displayed_article.title,
            "\n".join(
                window.article_list.list_widget.item(row).text()
                for row in range(window.article_list.list_widget.count())
            ),
        )

        with patch(
            "mercury.ui.main_window.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ) as clear_question:
            window._clear_visible_title_translations(article_ids)

        self.assertIn("2", clear_question.call_args.args[2])
        self.assertTrue(
            all(
                not article.translated_title
                for article in service.list_articles()
            )
        )
        self.assertEqual(service.translated_ids, provider_calls)
        self.assertIn("已恢复 2 个", window.statusBar().currentMessage())

        window.close()
        window.deleteLater()
        self.app.setStyleSheet("")


if __name__ == "__main__":
    unittest.main()
