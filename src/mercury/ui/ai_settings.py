from collections.abc import Callable

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from mercury.i18n import Translator
from mercury.llm import ProviderConfig, ProviderConnectionResult
from mercury.llm.config import MAX_TIMEOUT_SECONDS, MIN_TIMEOUT_SECONDS
from mercury.ui.provider_presets import (
    CUSTOM_PRESET_ID,
    PROVIDER_PRESETS,
    find_matching_preset,
    preset_by_id,
)


ConnectionTester = Callable[[ProviderConfig], ProviderConnectionResult]


class AISettingsDialog(QDialog):
    """Provider-neutral AI settings with explicit privacy messaging."""

    def __init__(
        self,
        translator: Translator,
        current_config: ProviderConfig | None = None,
        connection_tester: ConnectionTester | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._translator = translator
        self._connection_tester = connection_tester
        config = current_config or ProviderConfig()

        self.setMinimumWidth(480)

        self.provider_preset_combo = QComboBox()
        for preset in PROVIDER_PRESETS:
            self.provider_preset_combo.addItem(
                translator.text(preset.name_key),
                preset.identifier,
            )

        matching_preset = find_matching_preset(config)
        matching_index = self.provider_preset_combo.findData(
            matching_preset.identifier
        )
        self.provider_preset_combo.setCurrentIndex(matching_index)

        self.preset_notice = QLabel()
        self.preset_notice.setObjectName("AIProviderPresetNotice")
        self.preset_notice.setWordWrap(True)

        self.base_url_edit = QLineEdit(config.base_url)
        self.base_url_edit.setPlaceholderText(
            translator.text("ai_settings.base_url_placeholder")
        )
        self.base_url_edit.setToolTip(
            translator.text("ai_settings.base_url_tooltip")
        )
        self.model_edit = QLineEdit(config.model)
        self.api_key_edit = QLineEdit(config.api_key)
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(
            MIN_TIMEOUT_SECONDS,
            MAX_TIMEOUT_SECONDS,
        )
        self.timeout_spin.setDecimals(1)
        self.timeout_spin.setSingleStep(5.0)
        self.timeout_spin.setSuffix(" s")
        self.timeout_spin.setValue(config.timeout_seconds)

        self.privacy_notice = QLabel()
        self.privacy_notice.setObjectName("AIPrivacyNotice")
        self.privacy_notice.setWordWrap(True)

        self.test_connection_button = QPushButton()
        self.test_connection_button.clicked.connect(self._test_connection)

        self.connection_status = QLabel()
        self.connection_status.setObjectName("AIConnectionStatus")
        self.connection_status.setWordWrap(True)

        form_layout = QFormLayout()
        form_layout.addRow(
            self._translator.text("ai_settings.preset"),
            self.provider_preset_combo,
        )
        form_layout.addRow(
            self._translator.text("ai_settings.base_url"),
            self.base_url_edit,
        )
        form_layout.addRow(
            self._translator.text("ai_settings.model"),
            self.model_edit,
        )
        form_layout.addRow(
            self._translator.text("ai_settings.api_key"),
            self.api_key_edit,
        )
        form_layout.addRow(
            self._translator.text("ai_settings.timeout"),
            self.timeout_spin,
        )

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.preset_notice)
        main_layout.addWidget(self.privacy_notice)
        main_layout.addWidget(self.test_connection_button)
        main_layout.addWidget(self.connection_status)
        main_layout.addWidget(self.button_box)

        self.provider_preset_combo.currentIndexChanged.connect(
            self._apply_selected_preset
        )
        self.base_url_edit.textEdited.connect(self._mark_as_custom)
        self.model_edit.textEdited.connect(self._mark_as_custom)

        self._translate_ui()
        self._update_preset_notice(matching_preset.identifier)

    def selected_config(self) -> ProviderConfig:
        return ProviderConfig(
            base_url=self.base_url_edit.text().strip(),
            model=self.model_edit.text().strip(),
            api_key=self.api_key_edit.text(),
            timeout_seconds=self.timeout_spin.value(),
        )

    def accept(self) -> None:
        if self._validated_config() is None:
            return

        super().accept()

    def _validated_config(self) -> ProviderConfig | None:
        config = self.selected_config()

        if config.validation_errors():
            self.connection_status.setText(
                self._translator.text("ai_settings.invalid_config")
            )
            return None

        return config

    def _test_connection(self) -> None:
        config = self._validated_config()

        if config is None:
            return

        if self._connection_tester is None:
            self.connection_status.setText(
                self._translator.text("ai_settings.connection_unavailable")
            )
            return

        try:
            result = self._connection_tester(config)
        except Exception:
            self.connection_status.setText(
                self._translator.text("ai_settings.connection_failed")
            )
            return

        if result.success:
            self.connection_status.setText(
                self._translator.text("ai_settings.connection_success")
            )
            return

        message = self._redact_api_key(result.message)
        failure_text = self._translator.text(
            "ai_settings.connection_failed"
        )
        if message:
            failure_text = f"{failure_text} {message}"

        self.connection_status.setText(failure_text)

    def _redact_api_key(self, message: str) -> str:
        api_key = self.api_key_edit.text()

        if not api_key:
            return message

        return message.replace(api_key, "••••")

    def _apply_selected_preset(self, _index: int) -> None:
        identifier = self.provider_preset_combo.currentData()
        preset = preset_by_id(str(identifier))
        self._update_preset_notice(preset.identifier)
        self.connection_status.clear()

        if preset.config is None:
            return

        self.base_url_edit.setText(preset.config.base_url)
        self.model_edit.setText(preset.config.model)
        self.api_key_edit.clear()
        self.timeout_spin.setValue(preset.config.timeout_seconds)

    def _mark_as_custom(self, _text: str) -> None:
        if self.provider_preset_combo.currentData() == CUSTOM_PRESET_ID:
            return

        custom_index = self.provider_preset_combo.findData(
            CUSTOM_PRESET_ID
        )
        self.provider_preset_combo.setCurrentIndex(custom_index)

    def _update_preset_notice(self, identifier: str) -> None:
        preset = preset_by_id(identifier)
        self.preset_notice.setText(
            self._translator.text(preset.description_key)
        )

    def _translate_ui(self) -> None:
        self.setWindowTitle(self._translator.text("ai_settings.title"))
        self.privacy_notice.setText(
            self._translator.text("ai_settings.privacy_notice")
        )
        self.test_connection_button.setText(
            self._translator.text("ai_settings.test_connection")
        )

        ok_button = self.button_box.button(
            QDialogButtonBox.StandardButton.Ok
        )
        cancel_button = self.button_box.button(
            QDialogButtonBox.StandardButton.Cancel
        )
        ok_button.setText(self._translator.text("settings.ok"))
        cancel_button.setText(self._translator.text("settings.cancel"))
