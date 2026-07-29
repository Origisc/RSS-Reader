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

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit

from mercury.i18n import Translator
from mercury.llm import (
    InMemoryProviderConfigStore,
    MockLLMProvider,
    ProviderConfig,
    ProviderConnectionResult,
)
from mercury.services.mock_article_service import MockArticleService
from mercury.ui.ai_settings import AISettingsDialog, AgentsSettingsDialog
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
        self.assertIn("Base URL", dialog.connection_status.text())
        self.assertIn("Model name", dialog.connection_status.text())
        dialog.close()
        dialog.deleteLater()

    def test_remote_connection_failure_lists_vpn_and_dns_as_possible_causes(
        self,
    ) -> None:
        config = ProviderConfig(
            base_url="https://api.example.invalid/v1",
            model="remote-model",
        )
        dialog = AISettingsDialog(
            Translator("zh_CN"),
            config,
            connection_tester=lambda _config: ProviderConnectionResult(
                False,
                "Could not connect to Provider.",
            ),
        )

        dialog._test_connection()

        message = dialog.connection_status.text()
        self.assertIn("原因", message)
        self.assertIn("VPN/代理", message)
        self.assertIn("DNS", message)
        self.assertIn("Base URL", message)
        dialog.close()
        dialog.deleteLater()

    def test_local_connection_failure_points_to_local_service_and_port(
        self,
    ) -> None:
        config = ProviderConfig(
            base_url="http://127.0.0.1:11434/v1",
            model="local-model",
        )
        dialog = AISettingsDialog(
            Translator("zh_CN"),
            config,
            connection_tester=lambda _config: ProviderConnectionResult(
                False,
                "Could not connect to Provider.",
            ),
        )

        dialog._test_connection()

        message = dialog.connection_status.text()
        self.assertIn("Ollama", message)
        self.assertIn("端口", message)
        self.assertNotIn("DNS", message)
        dialog.close()
        dialog.deleteLater()

    def test_http_authentication_failure_explains_api_key_problem(self) -> None:
        dialog = AISettingsDialog(
            Translator("zh_CN"),
            self._valid_config(),
            connection_tester=lambda _config: ProviderConnectionResult(
                False,
                "Provider request failed with HTTP status 401.",
            ),
        )

        dialog._test_connection()

        self.assertIn("API Key", dialog.connection_status.text())
        self.assertIn("无效", dialog.connection_status.text())
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
        message = dialog.connection_status.text()
        self.assertIn("原因", message)
        self.assertIn("Base URL", message)
        self.assertIn("模型名称", message)
        dialog.close()
        dialog.deleteLater()


class AgentsSettingsDialogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def _config(self, model: str) -> ProviderConfig:
        return ProviderConfig(
            base_url="http://127.0.0.1:8080/v1",
            model=model,
            api_key=f"{model}-secret",
        )

    def test_each_agent_has_an_independent_provider_editor(self) -> None:
        configs = {
            "summary": self._config("summary-model"),
            "translation": self._config("translation-model"),
            "tag": self._config("tag-model"),
        }
        dialog = AgentsSettingsDialog(
            Translator("en_US"),
            current_configs=configs,
            initial_agent="translation",
        )

        self.assertEqual(dialog.agent_list.count(), 3)
        self.assertEqual(dialog.agent_list.currentRow(), 1)
        self.assertEqual(
            dialog.editors["summary"].model_edit.text(),
            "summary-model",
        )
        self.assertEqual(
            dialog.editors["translation"].model_edit.text(),
            "translation-model",
        )
        self.assertEqual(
            dialog.editors["tag"].model_edit.text(),
            "tag-model",
        )
        self.assertEqual(dialog.selected_configs(), configs)
        dialog.close()
        dialog.deleteLater()

    def test_agent_navigation_is_compact_and_evenly_sized(self) -> None:
        dialog = AgentsSettingsDialog(Translator("zh_CN"))

        self.assertEqual(dialog.agent_list.width(), 176)
        self.assertTrue(dialog.agent_list.uniformItemSizes())
        self.assertEqual(dialog.agent_list.spacing(), 4)
        self.assertEqual(
            dialog.agent_list.verticalScrollBarPolicy(),
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.assertEqual(
            [
                dialog.agent_list.item(index).sizeHint().height()
                for index in range(dialog.agent_list.count())
            ],
            [40, 40, 40],
        )
        dialog.close()
        dialog.deleteLater()

    def test_agent_can_be_disabled_without_blocking_other_agents(self) -> None:
        summary = self._config("summary-model")
        dialog = AgentsSettingsDialog(
            Translator("zh_CN"),
            current_configs={"summary": summary},
        )

        selected = dialog.selected_configs()

        self.assertEqual(selected["summary"], summary)
        self.assertIsNone(selected["translation"])
        self.assertIsNone(selected["tag"])
        dialog.accept()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
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

            def selected_configs(self):
                return {
                    "summary": config,
                    "translation": None,
                    "tag": None,
                }

        window = MainWindow(
            MockArticleService(),
            provider_config_store=store,
        )

        with patch(
            "mercury.ui.main_window.AgentsSettingsDialog",
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

            def selected_configs(self):
                return {
                    "summary": config,
                    "translation": None,
                    "tag": None,
                }

        window = MainWindow(
            MockArticleService(),
            provider_config_store=FailingStore(),
        )

        with (
            patch(
                "mercury.ui.main_window.AgentsSettingsDialog",
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

    def test_storage_load_permission_failure_reports_exact_reason(self) -> None:
        class UnreadableStore:
            def load(self):
                raise PermissionError("private filesystem details")

            def save(self, _config) -> None:
                pass

            def clear(self) -> None:
                pass

        window = MainWindow(
            MockArticleService(),
            provider_config_store=UnreadableStore(),
        )

        with patch(
            "mercury.ui.main_window.QMessageBox.warning"
        ) as warning:
            window._open_ai_settings()

        message = window.statusBar().currentMessage()
        self.assertIn("无法读取", message)
        self.assertIn("读取权限", message)
        self.assertNotIn("private filesystem", message)
        warning.assert_called_once()
        window.close()
        window.deleteLater()

    def test_saves_distinct_configs_to_each_agent_store(self) -> None:
        stores = {
            agent_id: InMemoryProviderConfigStore()
            for agent_id in ("summary", "translation", "tag")
        }
        configs = {
            agent_id: ProviderConfig(
                base_url="http://127.0.0.1:8080/v1",
                model=f"{agent_id}-model",
            )
            for agent_id in stores
        }

        class AcceptedDialog:
            def __init__(self, *args, **kwargs) -> None:
                pass

            def exec(self) -> int:
                return 1

            def selected_configs(self):
                return configs

        window = MainWindow(
            MockArticleService(),
            agent_provider_config_stores=stores,
        )
        with patch(
            "mercury.ui.main_window.AgentsSettingsDialog",
            AcceptedDialog,
        ):
            window._open_ai_settings("tag")

        self.assertEqual(
            {
                agent_id: store.load()
                for agent_id, store in stores.items()
            },
            configs,
        )
        window.close()
        window.deleteLater()

    def test_agent_entry_opens_the_matching_settings_page(self) -> None:
        opened_agents: list[str] = []

        class RejectedDialog:
            def __init__(self, *args, **kwargs) -> None:
                opened_agents.append(kwargs["initial_agent"])

            def exec(self) -> int:
                return 0

        window = MainWindow(MockArticleService())
        with patch(
            "mercury.ui.main_window.AgentsSettingsDialog",
            RejectedDialog,
        ):
            window._open_ai_settings("translation")
            window._open_ai_settings("tag")

        self.assertEqual(opened_agents, ["translation", "tag"])
        window.close()
        window.deleteLater()


if __name__ == "__main__":
    unittest.main()
