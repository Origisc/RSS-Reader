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

from PySide6.QtWidgets import QApplication, QDialog, QLineEdit

from mercury.i18n import Translator
from mercury.llm import (
    InMemoryProviderConfigStore,
    MockLLMProvider,
    ProviderConfig,
    ProviderConnectionResult,
)
from mercury.services.mock_article_service import MockArticleService
from mercury.ui.ai_settings import AISettingsDialog
from mercury.ui.main_window import MainWindow


class AISettingsDialogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def tearDown(self) -> None:
        self.app.setStyleSheet("")

    def _valid_config(self, api_key: str = "local-test-secret") -> ProviderConfig:
        return ProviderConfig(
            base_url="http://127.0.0.1:8080/v1",
            model="user-selected-model",
            api_key=api_key,
            timeout_seconds=45,
        )

    def test_loads_config_and_masks_api_key(self) -> None:
        config = self._valid_config()
        dialog = AISettingsDialog(Translator("en_US"), config)

        self.assertEqual(dialog.base_url_edit.text(), config.base_url)
        self.assertEqual(dialog.model_edit.text(), config.model)
        self.assertEqual(
            dialog.api_key_edit.echoMode(),
            QLineEdit.EchoMode.Password,
        )
        self.assertIn(
            "/chat/completions",
            dialog.base_url_edit.toolTip(),
        )
        self.assertNotIn(config.api_key, dialog.connection_status.text())
        dialog.close()
        dialog.deleteLater()

    def test_returns_provider_neutral_config(self) -> None:
        dialog = AISettingsDialog(Translator("zh_CN"), self._valid_config())

        self.assertEqual(dialog.selected_config(), self._valid_config())
        dialog.close()
        dialog.deleteLater()

    def test_local_deepseek_preset_configures_ollama_without_key(
        self,
    ) -> None:
        dialog = AISettingsDialog(
            Translator("zh_CN"),
            self._valid_config("must-be-cleared"),
        )

        preset_index = dialog.provider_preset_combo.findData(
            "ollama-local-deepseek"
        )
        dialog.provider_preset_combo.setCurrentIndex(preset_index)
        config = dialog.selected_config()

        self.assertEqual(
            config.base_url,
            "http://127.0.0.1:11434/v1",
        )
        self.assertEqual(config.model, "deepseek-r1:1.5b")
        self.assertEqual(config.api_key, "")
        self.assertEqual(config.timeout_seconds, 120.0)
        self.assertIn("零 API 费用", dialog.preset_notice.text())
        self.assertIn("ollama pull", dialog.preset_notice.text())
        dialog.close()
        dialog.deleteLater()

    def test_local_qwen_preset_configures_recommended_translation_model(
        self,
    ) -> None:
        dialog = AISettingsDialog(
            Translator("zh_CN"),
            self._valid_config("must-be-cleared"),
        )

        preset_index = dialog.provider_preset_combo.findData(
            "ollama-local-qwen25-7b"
        )
        self.assertGreaterEqual(preset_index, 0)

        dialog.provider_preset_combo.setCurrentIndex(preset_index)
        config = dialog.selected_config()

        self.assertEqual(
            config.base_url,
            "http://127.0.0.1:11434/v1",
        )
        self.assertEqual(config.model, "qwen2.5:7b-instruct")
        self.assertEqual(config.api_key, "")
        self.assertEqual(config.timeout_seconds, 120.0)
        self.assertIn("推荐用于中英翻译", dialog.preset_notice.text())
        self.assertIn(
            "ollama pull qwen2.5:7b-instruct",
            dialog.preset_notice.text(),
        )
        dialog.close()
        dialog.deleteLater()

    def test_deepseek_api_preset_is_explicitly_paid_and_clears_key(
        self,
    ) -> None:
        dialog = AISettingsDialog(
            Translator("en_US"),
            self._valid_config("wrong-provider-secret"),
        )

        preset_index = dialog.provider_preset_combo.findData(
            "deepseek-api"
        )
        dialog.provider_preset_combo.setCurrentIndex(preset_index)
        config = dialog.selected_config()

        self.assertEqual(config.base_url, "https://api.deepseek.com")
        self.assertEqual(config.model, "deepseek-v4-flash")
        self.assertEqual(config.api_key, "")
        self.assertIn("paid cloud API", dialog.preset_notice.text())
        dialog.close()
        dialog.deleteLater()

    def test_editing_preset_endpoint_switches_back_to_custom(self) -> None:
        dialog = AISettingsDialog(Translator("en_US"))
        preset_index = dialog.provider_preset_combo.findData(
            "ollama-local-deepseek"
        )
        dialog.provider_preset_combo.setCurrentIndex(preset_index)

        dialog.base_url_edit.setText("http://localhost:9000/v1")
        dialog.base_url_edit.textEdited.emit(
            "http://localhost:9000/v1"
        )

        self.assertEqual(
            dialog.provider_preset_combo.currentData(),
            "custom",
        )
        self.assertEqual(
            dialog.base_url_edit.text(),
            "http://localhost:9000/v1",
        )
        dialog.close()
        dialog.deleteLater()

    def test_existing_local_config_selects_matching_preset(self) -> None:
        config = ProviderConfig(
            base_url="http://127.0.0.1:11434/v1/",
            model="deepseek-r1:1.5b",
        )

        dialog = AISettingsDialog(Translator("en_US"), config)

        self.assertEqual(
            dialog.provider_preset_combo.currentData(),
            "ollama-local-deepseek",
        )
        self.assertEqual(dialog.selected_config(), config)
        dialog.close()
        dialog.deleteLater()

    def test_existing_qwen_config_selects_matching_preset(self) -> None:
        config = ProviderConfig(
            base_url="http://127.0.0.1:11434/v1/",
            model="qwen2.5:7b-instruct",
            timeout_seconds=120.0,
        )

        dialog = AISettingsDialog(Translator("en_US"), config)

        self.assertEqual(
            dialog.provider_preset_combo.currentData(),
            "ollama-local-qwen25-7b",
        )
        self.assertEqual(dialog.selected_config(), config)
        dialog.close()
        dialog.deleteLater()

    def test_mock_provider_can_pass_connection_test(self) -> None:
        dialog = AISettingsDialog(
            Translator("en_US"),
            self._valid_config(),
            connection_tester=lambda config: MockLLMProvider(
                config=config
            ).test_connection(),
        )

        dialog._test_connection()

        self.assertEqual(
            dialog.connection_status.text(),
            "Connection test succeeded.",
        )
        dialog.close()
        dialog.deleteLater()

    def test_missing_adapter_does_not_pretend_to_connect(self) -> None:
        dialog = AISettingsDialog(
            Translator("en_US"),
            self._valid_config(),
        )

        dialog._test_connection()

        self.assertIn("not sent", dialog.connection_status.text())
        dialog.close()
        dialog.deleteLater()

    def test_invalid_config_never_calls_connection_tester(self) -> None:
        received_configs: list[ProviderConfig] = []
        dialog = AISettingsDialog(
            Translator("en_US"),
            connection_tester=lambda config: (
                received_configs.append(config)
                or ProviderConnectionResult(True, "unexpected")
            ),
        )

        dialog._test_connection()

        self.assertEqual(received_configs, [])
        self.assertIn("valid Base URL", dialog.connection_status.text())
        dialog.close()
        dialog.deleteLater()

    def test_failed_result_redacts_full_api_key(self) -> None:
        secret = "never-show-this-key"
        dialog = AISettingsDialog(
            Translator("en_US"),
            self._valid_config(secret),
            connection_tester=lambda config: ProviderConnectionResult(
                False,
                f"Rejected credential {config.api_key}",
            ),
        )

        dialog._test_connection()

        self.assertNotIn(secret, dialog.connection_status.text())
        self.assertIn("••••", dialog.connection_status.text())
        dialog.close()
        dialog.deleteLater()

    def test_invalid_config_cannot_be_accepted(self) -> None:
        dialog = AISettingsDialog(Translator("zh_CN"))

        dialog.accept()

        self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected)
        self.assertTrue(dialog.connection_status.text())
        dialog.close()
        dialog.deleteLater()


class MainWindowAISettingsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_basic_reading_loads_without_provider_config(self) -> None:
        window = MainWindow(
            MockArticleService(),
            provider_config_store=InMemoryProviderConfigStore(),
        )

        self.assertEqual(window.article_list.list_widget.count(), 3)
        self.assertTrue(window.open_ai_settings_action.text())
        window.close()
        window.deleteLater()

    def test_accepted_dialog_saves_config_through_store(self) -> None:
        store = InMemoryProviderConfigStore()
        config = ProviderConfig(
            base_url="https://example.invalid/v1",
            model="saved-model",
            api_key="saved-secret",
        )

        class AcceptedDialog:
            def __init__(self, *args, **kwargs) -> None:
                pass

            def exec(self) -> int:
                return 1

            def selected_config(self) -> ProviderConfig:
                return config

        window = MainWindow(
            MockArticleService(),
            provider_config_store=store,
        )

        with patch(
            "mercury.ui.main_window.AISettingsDialog",
            AcceptedDialog,
        ):
            window._open_ai_settings()

        self.assertEqual(store.load(), config)
        self.assertNotIn(config.api_key, window.statusBar().currentMessage())
        window.close()
        window.deleteLater()

    def test_storage_failure_is_readable_and_does_not_crash_reader(
        self,
    ) -> None:
        config = ProviderConfig(
            base_url="https://example.invalid/v1",
            model="saved-model",
            api_key="must-not-appear",
        )

        class FailingStore:
            def load(self):
                return None

            def save(self, _config) -> None:
                raise OSError("database details must stay internal")

            def clear(self) -> None:
                pass

        class AcceptedDialog:
            def __init__(self, *args, **kwargs) -> None:
                pass

            def exec(self) -> int:
                return 1

            def selected_config(self) -> ProviderConfig:
                return config

        window = MainWindow(
            MockArticleService(),
            provider_config_store=FailingStore(),
        )

        with (
            patch(
                "mercury.ui.main_window.AISettingsDialog",
                AcceptedDialog,
            ),
            patch(
                "mercury.ui.main_window.QMessageBox.warning"
            ) as warning,
        ):
            window._open_ai_settings()

        message = window.statusBar().currentMessage()
        self.assertIn("保存到本地", message)
        self.assertNotIn(config.api_key, message)
        self.assertNotIn("database details", message)
        self.assertEqual(window.article_list.list_widget.count(), 3)
        warning.assert_called_once()
        window.close()
        window.deleteLater()


if __name__ == "__main__":
    unittest.main()
